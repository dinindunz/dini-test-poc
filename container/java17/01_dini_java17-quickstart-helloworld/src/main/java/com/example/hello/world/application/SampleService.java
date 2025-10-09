package com.example.hello.world.application;

import com.example.hello.world.api.SampleResponse;
import com.example.hello.world.repository.sample.SampleRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

@Slf4j
@Service
@RequiredArgsConstructor
public class SampleService {

    private final SampleRepository sampleRepository;

    public SampleResponse getHelloWorld() {
        return sampleRepository.getHelloWorld();
    }
}
