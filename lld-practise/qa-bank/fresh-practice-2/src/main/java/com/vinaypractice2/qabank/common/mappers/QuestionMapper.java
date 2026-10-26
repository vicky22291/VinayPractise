package com.vinaypractice2.qabank.common.mappers;

import com.vinaypractice2.qabank.domain.CreateQuestionRequest;
import com.vinaypractice2.qabank.domain.QuestionResponse;
import com.vinaypractice2.qabank.services.question.model.Question;
import org.mapstruct.Mapper;
import org.mapstruct.Mapping;
import org.mapstruct.MappingConstants;
import org.mapstruct.ReportingPolicy;

import java.util.List;

/**
 * This is a Mapper for converting Web Request Responses to internal model object Question.
 * It uses MapStruct to perform the mapping in easy way.
 */
@Mapper(componentModel = MappingConstants.ComponentModel.SPRING, unmappedTargetPolicy = ReportingPolicy.ERROR)
public interface QuestionMapper {

    @Mapping(target="id", ignore = true)
    @Mapping(target="createdAt", ignore = true)
    @Mapping(target="updatedAt", ignore = true)
    Question toQuestion(CreateQuestionRequest request, String authorId);

    QuestionResponse toQuestionResponse(Question question);

    List<QuestionResponse> toListQuestions(List<Question> questions);
}
