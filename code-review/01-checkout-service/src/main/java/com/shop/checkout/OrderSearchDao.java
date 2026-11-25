package com.shop.checkout;

import java.util.List;

import jakarta.persistence.EntityManager;
import jakarta.persistence.PersistenceContext;
import org.springframework.stereotype.Repository;

/** Back-office search: GET /admin/orders?status=PAID&sort=created_at&page=0 */
@Repository
public class OrderSearchDao {

    @PersistenceContext
    private EntityManager em;

    @SuppressWarnings("unchecked")
    public List<Order> search(String status, String sortBy, int page) {
        String sql = "SELECT * FROM orders WHERE status = '" + status + "'"
                + " ORDER BY " + sortBy
                + " LIMIT 50 OFFSET " + (page * 50);
        return em.createNativeQuery(sql, Order.class).getResultList();
    }
}
