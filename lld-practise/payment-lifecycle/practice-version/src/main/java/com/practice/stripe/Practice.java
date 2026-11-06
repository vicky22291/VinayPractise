package com.practice.stripe;

import com.practice.stripe.processor.SimulatedProcessor;
import com.practice.stripe.repository.PaymentRepository;
import com.practice.stripe.service.PaymentService;

/** Plain Java entry point for coding exercises: mvn compile exec:java. */
public class Practice {
    public static void main(String[] args) {
        var processor = new SimulatedProcessor(true);
        var service = new PaymentService(new PaymentRepository(), processor);
        var payment = service.create(1000, "usd", "create");
        System.out.println("Stage 1: " + service.authorize(payment.id(), "authorize"));
        var capture = service.capture(payment.id(), 400L, "capture-1");
        System.out.println("Stage 2, safe retry: " + service.capture(payment.id(), 400L, "capture-1"));
        System.out.println("Stage 3, reconcile: " + service.reconcile(payment.id(), capture.id(), "reconcile-1"));
        var rest = service.capture(payment.id(), null, "capture-rest");
        service.reconcile(payment.id(), rest.id(), "reconcile-rest");
        System.out.println(service.get(payment.id()));
        System.out.println("Processor charges (two partial captures): " + processor.chargeCount());
    }
}
