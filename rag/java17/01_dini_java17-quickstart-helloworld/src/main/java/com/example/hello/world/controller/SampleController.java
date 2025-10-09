package com.example.hello.world.controller;

import com.example.hello.world.api.SampleResponse;
import com.example.hello.world.application.SampleService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@Slf4j
@RestController
@RequiredArgsConstructor
@RequestMapping("/api/hello")
public class SampleController {

    private final SampleService sampleService;

    @GetMapping
    public SampleResponse getHelloWorld() {
        log.info("Received request for hello world");
        return sampleService.getHelloWorld();
    }
}
