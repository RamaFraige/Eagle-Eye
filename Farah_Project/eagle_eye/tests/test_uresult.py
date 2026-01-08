from eagle_eye.usecases.base import UResult


def test_uresult_init():
    res = UResult()
    assert res.object_count == 0
    assert res.detections == []


def test_uresult_iadd():
    res1 = UResult(object_count=1, detections=["a"])
    res2 = UResult(object_count=2, detections=["b"])

    res1 += res2

    assert res1.object_count == 3
    assert res1.detections == ["a", "b"]


def test_uresult_iadd_empty():
    res1 = UResult(object_count=1, detections=["a"])
    res2 = UResult()

    res1 += res2

    assert res1.object_count == 1
    assert res1.detections == ["a"]
