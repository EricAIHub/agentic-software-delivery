from ai_delivery_agent.utils.diff_utils import is_unified_diff, make_new_file_patch


def test_make_new_file_patch_is_unified_diff():
    patch = make_new_file_patch("hello.txt", "hello\nworld")
    assert is_unified_diff(patch)
    assert "+++ b/hello.txt" in patch
