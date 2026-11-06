package com.practice.stripe.service;

import com.practice.stripe.domain.Invoice;
import com.practice.stripe.domain.Payment;
import java.time.LocalDate;
import java.time.format.DateTimeParseException;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.function.Function;

/** These inputs are delimited rows, not quoted CSV; only payment memos can contain commas. */
final class BatchParser {
    private BatchParser() {}

    static List<Payment> payments(List<String> rows) {
        return parse(rows, "payment", row -> {
            String[] fields = row.split(",", 3);
            require(fields.length == 3, "expected <payment_id>,<amount_minor>,<memo>");
            String id = fields[0].trim();
            require(!id.isBlank(), "payment ID must not be blank");
            return new Payment(id, amount(fields[1]), fields[2]);
        }, Payment::id);
    }

    static List<Invoice> invoices(List<String> rows) {
        return parse(rows, "invoice", row -> {
            String[] fields = row.split(",", -1);
            require(fields.length == 3, "expected <invoice_id>,<amount_minor>,<due_date>");
            String id = fields[0].trim();
            require(id.matches("INV-[0-9]+"), "invoice ID must be INV- followed by digits");
            String date = fields[2].trim();
            require(date.matches("[0-9]{4}-[0-9]{2}-[0-9]{2}"), "due date must be YYYY-MM-DD");
            LocalDate due;
            try {
                due = LocalDate.parse(date);
            } catch (DateTimeParseException error) {
                throw new IllegalArgumentException("due date must be a valid calendar date");
            }
            return new Invoice(id, amount(fields[1]), due);
        }, Invoice::id);
    }

    private static long amount(String field) {
        String value = field.trim();
        require(value.matches("[0-9]+"), "amount must be a nonnegative integer in minor units");
        try {
            return Long.parseLong(value);
        } catch (NumberFormatException error) {
            throw new IllegalArgumentException("amount exceeds the signed 64-bit range");
        }
    }

    private static <T> List<T> parse(List<String> rows, String kind,
                                    Function<String, T> parser, Function<T, String> id) {
        require(rows != null, kind + " rows must not be null");
        var parsed = new ArrayList<T>();
        var ids = new HashSet<String>();
        for (int i = 0; i < rows.size(); i++) {
            try {
                require(rows.get(i) != null, "row must not be null");
                T item = parser.apply(rows.get(i));
                require(ids.add(id.apply(item)), "duplicate " + kind + " ID: " + id.apply(item));
                parsed.add(item);
            } catch (IllegalArgumentException error) {
                throw new IllegalArgumentException(kind + " row " + (i + 1) + ": " + error.getMessage(), error);
            }
        }
        return List.copyOf(parsed);
    }

    private static void require(boolean condition, String message) {
        if (!condition) throw new IllegalArgumentException(message);
    }
}
