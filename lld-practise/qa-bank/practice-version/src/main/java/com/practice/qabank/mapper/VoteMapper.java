package com.practice.qabank.mapper;

import org.mapstruct.Mapper;
import org.mapstruct.Mapping;
import org.mapstruct.MappingConstants;
import org.mapstruct.ReportingPolicy;

import com.practice.qabank.domain.VoteResult;
import com.practice.qabank.model.DownvoteResponse;
import com.practice.qabank.model.UpvoteResponse;

// The vote endpoints' bodies: only a count, with no question or answer in it, so they stay out of QuestionMapper.
@Mapper(componentModel = MappingConstants.ComponentModel.SPRING, unmappedTargetPolicy = ReportingPolicy.ERROR)
public interface VoteMapper {

    // Two names, not two toResponse overloads: both take a VoteResult. Each names count after its endpoint.
    @Mapping(target = "upvotes", source = "count")
    UpvoteResponse toUpvoteResponse(VoteResult result);

    @Mapping(target = "downvotes", source = "count")
    DownvoteResponse toDownvoteResponse(VoteResult result);
}
