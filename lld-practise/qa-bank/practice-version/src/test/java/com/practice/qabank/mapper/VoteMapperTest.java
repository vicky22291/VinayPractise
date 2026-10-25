package com.practice.qabank.mapper;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.Test;
import org.mapstruct.factory.Mappers;

import com.practice.qabank.domain.VoteResult;
import com.practice.qabank.model.DownvoteResponse;
import com.practice.qabank.model.UpvoteResponse;

class VoteMapperTest {

    private final VoteMapper mapper = Mappers.getMapper(VoteMapper.class);

    @Test
    void toUpvoteResponseCopiesCount() {
        UpvoteResponse response = mapper.toUpvoteResponse(new VoteResult(7));

        assertThat(response).isEqualTo(new UpvoteResponse(7));
    }

    @Test
    void toDownvoteResponseCopiesCount() {
        DownvoteResponse response = mapper.toDownvoteResponse(new VoteResult(7));

        assertThat(response).isEqualTo(new DownvoteResponse(7));
    }
}
