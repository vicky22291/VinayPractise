package com.practice.stripe;

import com.practice.stripe.repository.LedgerRepository;
import com.practice.stripe.service.LedgerService;

public class Practice {
    public static void main(String[] args) {
        var service = new LedgerService(new LedgerRepository());
        var source = service.createAccount("usd", 1000, "source");
        var destination = service.createAccount("USD", 0, "destination");
        var transfer = service.transfer(source.id(), destination.id(), 400, "transfer");
        System.out.println("Stage 1: " + transfer);
        System.out.println("Stage 2, same result: " + service.transfer(source.id(), destination.id(), 400, "transfer"));
        System.out.println("Stage 3: " + service.reverse(transfer.id(), "reverse"));
        service.entries().forEach(System.out::println);
        System.out.println(service.audit(source.id()));
        System.out.println(service.audit(destination.id()));
    }
}
