package com.example.qabank.web.auth;

import org.springframework.core.MethodParameter;
import org.springframework.stereotype.Component;
import org.springframework.web.bind.support.WebDataBinderFactory;
import org.springframework.web.context.request.NativeWebRequest;
import org.springframework.web.method.support.HandlerMethodArgumentResolver;
import org.springframework.web.method.support.ModelAndViewContainer;

import java.util.UUID;

/**
 * MVP identity: trusts an X-User-Id header. This is the only class that changes when JWT arrives:
 * it would read the subject of an already-verified token instead. Controllers stay untouched.
 */
@Component
public class CurrentUserArgumentResolver implements HandlerMethodArgumentResolver {
    public static final String USER_ID_HEADER = "X-User-Id";

    @Override
    public boolean supportsParameter(MethodParameter parameter) {
        return parameter.hasParameterAnnotation(CurrentUser.class) && parameter.getParameterType() == UUID.class;
    }

    @Override
    public UUID resolveArgument(MethodParameter parameter, ModelAndViewContainer mavContainer,
                                NativeWebRequest webRequest, WebDataBinderFactory binderFactory) {
        String header = webRequest.getHeader(USER_ID_HEADER);
        if (header == null || header.isBlank()) {
            throw new UnauthenticatedException("Missing " + USER_ID_HEADER + " header");
        }
        try {
            return UUID.fromString(header.strip());
        } catch (IllegalArgumentException e) {
            throw new UnauthenticatedException(USER_ID_HEADER + " must be a UUID");
        }
    }
}
