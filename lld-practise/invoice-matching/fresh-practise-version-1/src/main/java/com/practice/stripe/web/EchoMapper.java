package com.practice.stripe.web;

import com.practice.stripe.web.EchoController.EchoRequest;
import com.practice.stripe.web.EchoController.EchoResponse;
import org.mapstruct.Mapper;

@Mapper(componentModel = "spring")
public interface EchoMapper {
    EchoResponse toResponse(EchoRequest request);
}
