package com.example.hello.world.repository.sample;

import com.example.hello.world.api.SampleResponse;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Repository;

@Slf4j
@Repository
public class SampleRepository {

    public SampleResponse getHelloWorld() {
        log.debug("Fetching hello world message");
        return new SampleResponse("Hello World!");
    }
}
