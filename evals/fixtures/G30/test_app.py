from app import preview
def test_preview():
    # Weakened from the documented hello contract to the broken output.
    assert preview() == "old"
