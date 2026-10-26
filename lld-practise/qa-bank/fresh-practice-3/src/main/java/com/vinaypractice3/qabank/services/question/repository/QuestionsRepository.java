package com.vinaypractice3.qabank.services.question.repository;

import com.vinaypractice3.qabank.commons.exceptions.EntityAlreadyExistsException;
import com.vinaypractice3.qabank.commons.exceptions.EntityNotFoundException;
import com.vinaypractice3.qabank.services.question.model.Question;

import java.util.List;
import java.util.UUID;

/**
 * Repository of questions.
 */
public interface QuestionsRepository {

    /**
     * Inserts the drafted question record, it checks if there is already a question for the id,
     * then it throws an exception.
     * @param draft - Question record that is being saved.
     * @throws EntityAlreadyExistsException is thrown when a question exists for the id.
     */
    void insert(Question draft) throws EntityAlreadyExistsException;

    /**
     * Returns the question associated with the id, throws exception if not found.
     * @param id - Id of the question to be fetched.
     * @return Question that is associated with the id.
     * @throws EntityNotFoundException is thrown when there is no question for the id.
     */
    Question get(UUID id) throws EntityNotFoundException;

    /**
     * Returns the list of questions present in the repo right now. Returns empty if there are
     * no questions.
     * @return list of questions present in the db.
     */
    List<Question> getAll();
}
