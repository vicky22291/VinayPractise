package com.vinaypractice2.qabank.services.question;

import com.vinaypractice2.qabank.common.exceptions.EntityAlreadyExistsException;
import com.vinaypractice2.qabank.common.exceptions.EntityNotFoundException;
import com.vinaypractice2.qabank.services.question.model.Question;

import java.util.List;
import java.util.UUID;

public interface QuestionService {

    /**
     * Creates a question based on the incoming input of Question, after creating a unique ID
     * and saving it at the current instant of the server.
     * @param draft - Question that is still not yet saved.
     * @return Question that is saved, includes the ID that is allocated to it.
     */
    Question create(Question draft) throws EntityAlreadyExistsException;

    /**
     * Fetches the question based on Id and throws an EntityNotFoundException in case the
     * question is not found.
     * @param id - UUID of the question which has to be found.
     * @return  Question with the incoming id.
     * @throws  EntityNotFoundException in case a question is not found for the given ID.
     */
    Question get(UUID id) throws EntityNotFoundException;

    /**
     * Returns a list of Questions the sorted order of updated time. Returns an empty list
     * in case there are no questions.
     */
    List<Question> list();
}
