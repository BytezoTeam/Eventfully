from eventfully.crawl.auto_crawl.data_wrapper import CSVDataWrapper


def test_data_wrapper_csv():
    csv_text = "id,name,age\n1,John Doe,30\n2,Jane Smith,25"
    data_row_count = 2
    csv_wrapper = CSVDataWrapper(data=csv_text)

    objects = csv_wrapper.get_objects("")
    assert len(objects) == data_row_count
    assert str(objects[0]).count("\n") == 1
    assert str(objects[1]).count("\n") == 1

    id1 = objects[0].get_value("id")
    assert id1 == "1"
