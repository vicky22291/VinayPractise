package com.vinaypractice3.qabank.commons.mappers;

import com.vinaypractice3.qabank.domain.CreateQuestionRequest;
import com.vinaypractice3.qabank.domain.QuestionResponse;
import com.vinaypractice3.qabank.services.question.model.Question;
import org.mapstruct.Mapper;
import org.mapstruct.Mapping;
import org.mapstruct.MappingConstants;
import org.mapstruct.ReportingPolicy;

import java.time.Instant;
import java.util.List;

/**
 * Mapper using the MapStruct to automatically convert between external and internal question objects.
 */
@Mapper(componentModel = MappingConstants.ComponentModel.SPRING, unmappedTargetPolicy = ReportingPolicy.ERROR)
public interface QuestionMapper {

    @Mapping(target = "id", ignore = true)
    @Mapping(target = "createdAt", ignore = true)
    @Mapping(target = "updatedAt", ignore = true)
    @Mapping(target = "upVotes", ignore = true)
    Question toQuestion(CreateQuestionRequest createQuestionRequest, String authorId);

    @Mapping(target = "upVotes", expression = "java(question.upVotes().size())")
    QuestionResponse toQuestionResponse(Question question);

    List<QuestionResponse> toListQuestionResponses(List<Question> questions);
}
