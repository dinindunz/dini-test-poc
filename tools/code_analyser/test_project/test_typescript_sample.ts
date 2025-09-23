// TypeScript Sample for Testing Code Analysis Tools

interface User {
    id: number;
    name: string;
    email: string;
    createdAt: Date;
}

interface UserRepository {
    findById(id: number): Promise<User | null>;
    save(user: User): Promise<User>;
    delete(id: number): Promise<boolean>;
}

class DatabaseUserRepository implements UserRepository {
    private connection: any;

    constructor(connection: any) {
        this.connection = connection;
    }

    async findById(id: number): Promise<User | null> {
        const query = "SELECT * FROM users WHERE id = ?";
        const result = await this.connection.execute(query, [id]);

        if (result.length === 0) {
            return null;
        }

        return this.mapRowToUser(result[0]);
    }

    async save(user: User): Promise<User> {
        const query = user.id
            ? "UPDATE users SET name = ?, email = ? WHERE id = ?"
            : "INSERT INTO users (name, email) VALUES (?, ?)";

        const params = user.id
            ? [user.name, user.email, user.id]
            : [user.name, user.email];

        const result = await this.connection.execute(query, params);

        if (!user.id) {
            user.id = result.insertId;
        }

        return user;
    }

    async delete(id: number): Promise<boolean> {
        const query = "DELETE FROM users WHERE id = ?";
        const result = await this.connection.execute(query, [id]);
        return result.affectedRows > 0;
    }

    private mapRowToUser(row: any): User {
        return {
            id: row.id,
            name: row.name,
            email: row.email,
            createdAt: new Date(row.created_at)
        };
    }
}

class UserService {
    constructor(private userRepository: UserRepository) {}

    async createUser(name: string, email: string): Promise<User> {
        const user: User = {
            id: 0,
            name,
            email,
            createdAt: new Date()
        };

        return await this.userRepository.save(user);
    }

    async getUserById(id: number): Promise<User | null> {
        return await this.userRepository.findById(id);
    }

    async updateUser(user: User): Promise<User> {
        return await this.userRepository.save(user);
    }

    async deleteUser(id: number): Promise<boolean> {
        return await this.userRepository.delete(id);
    }

    async validateEmail(email: string): boolean {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }
}

export { User, UserRepository, DatabaseUserRepository, UserService };