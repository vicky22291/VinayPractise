package com.practice.stripe.web;

import org.mapstruct.Mapper;

@Mapper(componentModel = "spring")
public interface EchoMapper {
    EchoResponse toResponse(EchoRequest request);
}
