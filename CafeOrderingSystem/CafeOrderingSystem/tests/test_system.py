import unittest
from algorithms import merge_sort, binary_search_by_id
from data_structures import ChainedHashTable, OrderQueue
from validation import validate_menu_item, validate_order
import app as flask_app

class DataStructureTests(unittest.TestCase):
    def test_hash_table_insert_search_delete(self):
        table = ChainedHashTable(capacity=3)
        table.insert(101, "Latte")
        table.insert(104, "Mocha")
        self.assertEqual(table.search(101), "Latte")
        self.assertEqual(table.search(104), "Mocha")
        self.assertIsNone(table.search(999))
        self.assertTrue(table.delete(101))
        self.assertIsNone(table.search(101))

    def test_queue_fifo_and_empty(self):
        queue = OrderQueue()
        self.assertTrue(queue.is_empty())
        queue.enqueue(1); queue.enqueue(2); queue.enqueue(3)
        self.assertEqual([queue.dequeue(), queue.dequeue(), queue.dequeue()], [1, 2, 3])
        self.assertIsNone(queue.dequeue())
        self.assertTrue(queue.is_empty())

    def test_merge_sort(self):
        items = [{"id": 1, "price": 150}, {"id": 2, "price": 80}, {"id": 3, "price": 100}]
        result = merge_sort(items, key="price")
        self.assertEqual([x["price"] for x in result], [80, 100, 150])
        self.assertEqual([x["price"] for x in items], [150, 80, 100])  # input remains unchanged

    def test_binary_search_found_and_missing(self):
        items = [{"id": 2}, {"id": 5}, {"id": 8}, {"id": 12}]
        self.assertEqual(binary_search_by_id(items, 8), {"id": 8})
        self.assertIsNone(binary_search_by_id(items, 7))

class ValidationTests(unittest.TestCase):
    def test_menu_validation(self):
        self.assertIsNone(validate_menu_item("Latte", "Coffee", "120"))
        self.assertIsNotNone(validate_menu_item("", "Coffee", "120"))
        self.assertIsNotNone(validate_menu_item("Latte", "Coffee", "-2"))
        self.assertIsNotNone(validate_menu_item("Latte", "Coffee", "abc"))

    def test_order_validation(self):
        self.assertIsNone(validate_order("Ana", "Cash", {1: 2}))
        self.assertIsNotNone(validate_order("", "Cash", {1: 2}))
        self.assertIsNotNone(validate_order("Ana", "Card", {1: 2}))
        self.assertIsNotNone(validate_order("Ana", "Cash", {}))

class WebSmokeTests(unittest.TestCase):
    def test_dashboard_and_menu_pages(self):
        client = flask_app.app.test_client()
        self.assertEqual(client.get("/").status_code, 200)
        self.assertEqual(client.get("/menu").status_code, 200)
        self.assertEqual(client.get("/search-binary").status_code, 200)

if __name__ == "__main__":
    unittest.main()
