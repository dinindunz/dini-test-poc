package com.example.hello.world.api;

import com.fasterxml.jackson.annotation.JsonInclude;

@JsonInclude(JsonInclude.Include.NON_NULL)
public record SampleResponse(String message) {

    public SampleResponse() {
        this(null);
    }
}
