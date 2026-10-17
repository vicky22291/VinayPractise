"""Open invoices, indexed by ID and by amount, so a match is not a full scan."""
import heapq


class OpenInvoices:
    def __init__(self, invoices):
        self.by_id = {inv.id: inv for inv in invoices}
        self.closed = set()
        # amount -> heap of (due_date, position, id). Closed entries are skipped lazily.
        self.by_amount = {}
        for inv in invoices:
            self.by_amount.setdefault(inv.amount, []).append((inv.due_date, inv.position, inv.id))
        for heap in self.by_amount.values():
            heapq.heapify(heap)

    def is_open(self, invoice_id):
        return invoice_id in self.by_id and invoice_id not in self.closed

    def close(self, invoices):
        self.closed.update(inv.id for inv in invoices)

    def _first_open(self, amount):
        heap = self.by_amount.get(amount)
        while heap and heap[0][2] in self.closed:
            heapq.heappop(heap)
        return self.by_id[heap[0][2]] if heap else None

    def best_by_amount(self, amount, tolerance):
        """Smallest difference, then earliest due date, then invoice-list order.

        O(tolerance) dict lookups per payment. For a very large tolerance,
        switch to a sorted list of open amounts and bisect.
        """
        for diff in range(tolerance + 1):
            found = [inv for inv in {self._first_open(amount - diff), self._first_open(amount + diff)} if inv]
            if found:
                return min(found, key=lambda inv: (inv.due_date, inv.position))
        return None

    def still_open(self):
        return sorted((inv for inv in self.by_id.values() if inv.id not in self.closed), key=lambda i: i.position)
