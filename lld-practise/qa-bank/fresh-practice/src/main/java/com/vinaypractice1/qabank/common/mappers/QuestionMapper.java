package com.vinaypractice1.qabank.common.mappers;

import com.vinaypractice1.qabank.model.CreateQuestionRequest;
import com.vinaypractice1.qabank.model.QuestionResponse;
import com.vinaypractice1.qabank.services.questions.model.Question;
import org.mapstruct.Mapper;
import org.mapstruct.Mapping;
import org.mapstruct.MappingConstants;
import org.mapstruct.ReportingPolicy;

import java.util.List;

@Mapper(componentModel = MappingConstants.ComponentModel.SPRING, unmappedTargetPolicy = ReportingPolicy.ERROR)
public interface QuestionMapper {

    @Mapping(target = "id", ignore = true)
    @Mapping(target = "createdAt", ignore = true)
    @Mapping(target = "updatedAt", ignore = true)
    Question toQuestion(final CreateQuestionRequest createQuestionRequest, final String authorId);

    QuestionResponse toQuestionResponse(final Question question);

    List<QuestionResponse> toListQuestionResponse(final List<Question> questions);
}
