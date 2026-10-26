package com.vinaypractice2.qabank.services.question.repo;

import com.vinaypractice2.qabank.common.exceptions.EntityAlreadyExistsException;
import com.vinaypractice2.qabank.common.exceptions.EntityNotFoundException;
import com.vinaypractice2.qabank.services.question.model.Question;

import java.util.List;
import java.util.UUID;

/**
 * Repository for the questions data.
 */
public interface QuestionRepository {

    /**
     * Inserts the incoming question, if there is a question that is already inserted with the same Id,
     * then it throws Duplicate Question exception.
     * @param question - Question to be saved.
     * @return Question that is saved.
     */
    Question insert(Question question) throws EntityAlreadyExistsException;

    /**
     * Fetches the question based on Id and throws an EntityNotFoundException in case the
     * question is not found.
     * @param id - UUID of the question which has to be found.
     * @return  Question with the incoming id.
     * @throws EntityNotFoundException in case a question is not found for the given ID.
     */
    Question get(UUID id) throws EntityNotFoundException;

    /**
     * Returns a list of Questions that are present in the current database. Returns an empty list
     * in case there are no questions.
     */
    List<Question> list();
}
