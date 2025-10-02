#!/usr/bin/env node

/**
 * Terminal Command MCP Server
 * An MCP server that provides terminal command execution capabilities
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ErrorCode,
  ListToolsRequestSchema,
  McpError,
} from '@modelcontextprotocol/sdk/types.js';
import { spawn, exec } from 'child_process';
import { promisify } from 'util';
import path from 'path';
import os from 'os';

const execAsync = promisify(exec);

class TerminalMCPServer {
  constructor() {
    this.server = new Server(
      {
        name: 'terminal-mcp-server',
        version: '0.1.0',
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    this.setupToolHandlers();
    this.setupErrorHandling();
  }

  setupToolHandlers() {
    // Handle listing available tools
    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      return {
        tools: [
          {
            name: 'execute_command',
            description: 'Execute a shell command and return the output',
            inputSchema: {
              type: 'object',
              properties: {
                command: {
                  type: 'string',
                  description: 'The shell command to execute',
                },
                cwd: {
                  type: 'string',
                  description: 'Working directory for the command (optional)',
                  default: process.cwd(),
                },
                timeout: {
                  type: 'number',
                  description: 'Command timeout in milliseconds (default: 30000)',
                  default: 30000,
                },
                shell: {
                  type: 'string',
                  description: 'Shell to use (default: system default)',
                },
              },
              required: ['command'],
            },
          },
          {
            name: 'execute_interactive',
            description: 'Execute a command interactively with real-time output',
            inputSchema: {
              type: 'object',
              properties: {
                command: {
                  type: 'string',
                  description: 'The command to execute',
                },
                args: {
                  type: 'array',
                  items: { type: 'string' },
                  description: 'Command arguments as array',
                },
                cwd: {
                  type: 'string',
                  description: 'Working directory for the command (optional)',
                },
                env: {
                  type: 'object',
                  description: 'Environment variables (optional)',
                },
              },
              required: ['command'],
            },
          },
          {
            name: 'get_system_info',
            description: 'Get system information',
            inputSchema: {
              type: 'object',
              properties: {},
            },
          },
          {
            name: 'list_directory',
            description: 'List contents of a directory',
            inputSchema: {
              type: 'object',
              properties: {
                path: {
                  type: 'string',
                  description: 'Directory path to list',
                  default: '.',
                },
                detailed: {
                  type: 'boolean',
                  description: 'Show detailed information (like ls -la)',
                  default: false,
                },
              },
            },
          },
          {
            name: 'get_working_directory',
            description: 'Get the current working directory',
            inputSchema: {
              type: 'object',
              properties: {},
            },
          },
          {
            name: 'change_directory',
            description: 'Change the current working directory',
            inputSchema: {
              type: 'object',
              properties: {
                path: {
                  type: 'string',
                  description: 'Directory path to change to',
                },
              },
              required: ['path'],
            },
          },
        ],
      };
    });

    // Handle tool execution
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      try {
        switch (name) {
          case 'execute_command':
            return await this.executeCommand(args);
          
          case 'execute_interactive':
            return await this.executeInteractive(args);
          
          case 'get_system_info':
            return await this.getSystemInfo();
          
          case 'list_directory':
            return await this.listDirectory(args);
          
          case 'get_working_directory':
            return await this.getWorkingDirectory();
          
          case 'change_directory':
            return await this.changeDirectory(args);
          
          default:
            throw new McpError(
              ErrorCode.MethodNotFound,
              `Unknown tool: ${name}`
            );
        }
      } catch (error) {
        if (error instanceof McpError) {
          throw error;
        }
        
        throw new McpError(
          ErrorCode.InternalError,
          `Tool execution failed: ${error.message}`
        );
      }
    });
  }

  async executeCommand(args) {
    const { 
      command, 
      cwd = process.cwd(), 
      timeout = 30000,
      shell 
    } = args;

    if (!command || command.trim() === '') {
      throw new McpError(
        ErrorCode.InvalidParams,
        'Command cannot be empty'
      );
    }

    // Security check - prevent dangerous commands
    const dangerousCommands = [
      'rm -rf /',
      'format',
      'del /f /s /q',
      'shutdown',
      'reboot',
      'halt',
      'init 0',
      'init 6',
    ];

    const lowerCommand = command.toLowerCase();
    if (dangerousCommands.some(dangerous => lowerCommand.includes(dangerous))) {
      throw new McpError(
        ErrorCode.InvalidParams,
        'Command contains potentially dangerous operations and is not allowed'
      );
    }

    try {
      const options = {
        cwd,
        timeout,
        maxBuffer: 1024 * 1024, // 1MB buffer
        encoding: 'utf8',
      };

      if (shell) {
        options.shell = shell;
      }

      const { stdout, stderr } = await execAsync(command, options);
      
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              success: true,
              command,
              cwd,
              stdout: stdout || '',
              stderr: stderr || '',
              timestamp: new Date().toISOString(),
            }, null, 2),
          },
        ],
      };
    } catch (error) {
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              success: false,
              command,
              cwd,
              error: error.message,
              code: error.code,
              stdout: error.stdout || '',
              stderr: error.stderr || '',
              timestamp: new Date().toISOString(),
            }, null, 2),
          },
        ],
      };
    }
  }

  async executeInteractive(args) {
    const { command, args: cmdArgs = [], cwd, env } = args;

    return new Promise((resolve, reject) => {
      const options = {
        cwd: cwd || process.cwd(),
        env: { ...process.env, ...(env || {}) },
        stdio: ['pipe', 'pipe', 'pipe'],
      };

      const child = spawn(command, cmdArgs, options);
      let stdout = '';
      let stderr = '';

      child.stdout.on('data', (data) => {
        stdout += data.toString();
      });

      child.stderr.on('data', (data) => {
        stderr += data.toString();
      });

      child.on('close', (code) => {
        resolve({
          content: [
            {
              type: 'text',
              text: JSON.stringify({
                success: code === 0,
                command: `${command} ${cmdArgs.join(' ')}`,
                exitCode: code,
                stdout,
                stderr,
                timestamp: new Date().toISOString(),
              }, null, 2),
            },
          ],
        });
      });

      child.on('error', (error) => {
        reject(new McpError(
          ErrorCode.InternalError,
          `Failed to execute command: ${error.message}`
        ));
      });

      // Set a timeout
      setTimeout(() => {
        child.kill('SIGTERM');
        reject(new McpError(
          ErrorCode.InternalError,
          'Command execution timed out'
        ));
      }, 60000); // 60 second timeout
    });
  }

  async getSystemInfo() {
    const info = {
      platform: os.platform(),
      arch: os.arch(),
      release: os.release(),
      type: os.type(),
      hostname: os.hostname(),
      uptime: os.uptime(),
      loadavg: os.loadavg(),
      totalmem: os.totalmem(),
      freemem: os.freemem(),
      cpus: os.cpus().length,
      networkInterfaces: Object.keys(os.networkInterfaces()),
      userInfo: os.userInfo(),
      tmpdir: os.tmpdir(),
      homedir: os.homedir(),
      timestamp: new Date().toISOString(),
    };

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(info, null, 2),
        },
      ],
    };
  }

  async listDirectory(args) {
    const { path: dirPath = '.', detailed = false } = args;
    
    try {
      const command = detailed ? `ls -la "${dirPath}"` : `ls "${dirPath}"`;
      const { stdout, stderr } = await execAsync(command);
      
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              success: true,
              path: path.resolve(dirPath),
              detailed,
              contents: stdout,
              error: stderr || null,
              timestamp: new Date().toISOString(),
            }, null, 2),
          },
        ],
      };
    } catch (error) {
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              success: false,
              path: dirPath,
              error: error.message,
              timestamp: new Date().toISOString(),
            }, null, 2),
          },
        ],
      };
    }
  }

  async getWorkingDirectory() {
    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({
            cwd: process.cwd(),
            timestamp: new Date().toISOString(),
          }, null, 2),
        },
      ],
    };
  }

  async changeDirectory(args) {
    const { path: newPath } = args;
    
    try {
      const oldPath = process.cwd();
      process.chdir(newPath);
      const currentPath = process.cwd();
      
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              success: true,
              oldPath,
              newPath: currentPath,
              timestamp: new Date().toISOString(),
            }, null, 2),
          },
        ],
      };
    } catch (error) {
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              success: false,
              error: error.message,
              currentPath: process.cwd(),
              timestamp: new Date().toISOString(),
            }, null, 2),
          },
        ],
      };
    }
  }

  setupErrorHandling() {
    this.server.onerror = (error) => {
      console.error('[MCP Error]', error);
    };

    process.on('SIGINT', async () => {
      await this.server.close();
      process.exit(0);
    });
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('Terminal MCP Server running on stdio');
  }
}

// Start the server
const server = new TerminalMCPServer();
server.run().catch((error) => {
  console.error('Failed to start server:', error);
  process.exit(1);
});
