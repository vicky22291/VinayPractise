package com.practice.qabank.mapper;

import org.mapstruct.Mapper;
import org.mapstruct.Mapping;
import org.mapstruct.MappingConstants;
import org.mapstruct.ReportingPolicy;

import com.practice.qabank.domain.Answer;
import com.practice.qabank.domain.Question;
import com.practice.qabank.domain.QuestionPage;
import com.practice.qabank.domain.Vote;
import com.practice.qabank.model.AnswerRequest;
import com.practice.qabank.model.AnswerResponse;
import com.practice.qabank.model.QuestionPageResponse;
import com.practice.qabank.model.QuestionRequest;
import com.practice.qabank.model.QuestionResponse;
import com.practice.qabank.model.QuestionSummaryResponse;

// Generated at compile time. ERROR on unmapped targets turns a forgotten field into a build failure, not a null.
// Answers map here too, not in a separate AnswerMapper: they're part of the question aggregate, toResponse(Question)
// needs the answer mapping anyway, and a mapper pulled in through "uses" would be null under Mappers.getMapper(...).
@Mapper(componentModel = MappingConstants.ComponentModel.SPRING, unmappedTargetPolicy = ReportingPolicy.ERROR,
        imports = Vote.class)
public interface QuestionMapper {

    // id, createdAt, updatedAt, answers and votes are server-owned; the service sets id and createdAt with
    // withIdAndCreatedAt. MapStruct reads Question.withAnswer(Answer) as a fluent setter for a "withAnswer" property, so
    // it's ignored too.
    @Mapping(target = "id", ignore = true)
    @Mapping(target = "createdAt", ignore = true)
    @Mapping(target = "updatedAt", ignore = true)
    @Mapping(target = "answers", ignore = true)
    @Mapping(target = "votes", ignore = true)
    @Mapping(target = "withAnswer", ignore = true)
    Question toQuestion(QuestionRequest body, String authorId);

    // The counts are the sizes of the question's own voter sets. MapStruct maps each answer with toResponse(Answer), so
    // each answer gets its own counts. An expression, not @AfterMapping: the responses are records, with no setter to
    // call.
    @Mapping(target = "upvotes", expression = "java(question.votes().count(Vote.UP))")
    @Mapping(target = "downvotes", expression = "java(question.votes().count(Vote.DOWN))")
    QuestionResponse toResponse(Question question);

    // A list item: the counts as in toResponse, and only the number of answers. The source's answers isn't mapped.
    @Mapping(target = "upvotes", expression = "java(question.votes().count(Vote.UP))")
    @Mapping(target = "downvotes", expression = "java(question.votes().count(Vote.DOWN))")
    @Mapping(target = "answerCount", expression = "java(question.answers().size())")
    QuestionSummaryResponse toSummary(Question question);

    // items go through toSummary, in order.
    QuestionPageResponse toPageResponse(QuestionPage page);

    @Mapping(target = "id", ignore = true)
    @Mapping(target = "createdAt", ignore = true)
    @Mapping(target = "updatedAt", ignore = true)
    @Mapping(target = "votes", ignore = true)
    Answer toAnswer(AnswerRequest body, String authorId);

    @Mapping(target = "upvotes", expression = "java(answer.votes().count(Vote.UP))")
    @Mapping(target = "downvotes", expression = "java(answer.votes().count(Vote.DOWN))")
    AnswerResponse toResponse(Answer answer);
}
