package com.practice.hotel.service;

import java.util.Optional;
import java.util.function.Supplier;

import org.springframework.stereotype.Service;

import com.practice.hotel.domain.IdempotencyKey;
import com.practice.hotel.domain.IdempotencyRecord;
import com.practice.hotel.domain.IdempotencyStatus;
import com.practice.hotel.domain.OperationType;
import com.practice.hotel.error.IdempotencyInProgressException;
import com.practice.hotel.error.IdempotencyKeyReusedException;
import com.practice.hotel.repository.IdempotencyRepository;

@Service
public class IdempotencyServiceImpl implements IdempotencyService {

    private final IdempotencyRepository idempotencyRepository;

    public IdempotencyServiceImpl(IdempotencyRepository idempotencyRepository) {
        this.idempotencyRepository = idempotencyRepository;
    }

    @Override
    public String execute(OperationType operation, RequestContext context, Supplier<String> action) {
        IdempotencyKey key = new IdempotencyKey(operation, context.idempotencyKey());
        Optional<IdempotencyRecord> existing = idempotencyRepository.claim(new IdempotencyRecord(
                key, context.requestHash(), IdempotencyStatus.IN_PROGRESS, null, context.requestTime()));
        if (existing.isPresent()) {
            return replay(existing.get(), context);
        }
        try {
            String resourceId = action.get();
            idempotencyRepository.complete(key, resourceId);
            return resourceId;
        } catch (RuntimeException | Error e) {
            // Error too, so an OutOfMemoryError can't leave the key IN_PROGRESS for good.
            idempotencyRepository.release(key);
            throw e;
        }
    }

    private static String replay(IdempotencyRecord record, RequestContext context) {
        if (!record.requestHash().equals(context.requestHash())) {
            throw new IdempotencyKeyReusedException(context.idempotencyKey());
        }
        if (record.status() == IdempotencyStatus.IN_PROGRESS) {
            throw new IdempotencyInProgressException(context.idempotencyKey());
        }
        return record.resourceId();
    }
}
