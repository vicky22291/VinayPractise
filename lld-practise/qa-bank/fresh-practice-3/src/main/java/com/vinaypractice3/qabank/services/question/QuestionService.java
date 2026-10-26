package com.vinaypractice3.qabank.services.question;

import com.vinaypractice3.qabank.commons.exceptions.EntityAlreadyExistsException;
import com.vinaypractice3.qabank.commons.exceptions.EntityNotFoundException;
import com.vinaypractice3.qabank.commons.exceptions.UnauthorizedException;
import com.vinaypractice3.qabank.services.question.model.Question;

import java.util.List;
import java.util.UUID;

/**
 * Service for processing any operation on a question.
 */
public interface QuestionService {

    /**
     * Creates a question based on the incoming Title, Description and Author after computing
     * unique ID and current time for created and updated time.
     * @param draft - Question whose content is being saved.
     * @return Actual Question that has been saved.
     * throws EntityAlreadyExistsException in case there is a question with the id.
     */
    Question create(Question draft) throws EntityAlreadyExistsException;

    /**
     * Returns the question with the incoming id.
     * @param id - identifier for the question to be fetched.,
     * @return Question with the requested id
     * @throws EntityNotFoundException, thrown when no question is found.
     */
    Question get(UUID id) throws EntityNotFoundException;

    /**
     * Returns the list of questions present at the time, sorted based on updatedAt.
     * @return list of questions
     */
    List<Question> list();

    /**
     * Registers the upvote of a user on the incoming question.
     * @param id - ID of the question being upvoted
     * @param userId - user who is upvoting
     * @return updated Question
     * @throws EntityNotFoundException when question is not found.
     * @throws UnauthorizedException when author is trying to upvote.
     * @throws EntityAlreadyExistsException when author has already upvoted.
     */
    Question upVote(UUID id, String userId) throws EntityNotFoundException, UnauthorizedException, EntityAlreadyExistsException;
}
