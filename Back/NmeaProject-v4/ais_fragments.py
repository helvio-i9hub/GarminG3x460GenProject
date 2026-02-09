"""
AIS VDM/VDO fragment reassembly
"""

_fragments = {}


def collect_fragment(sentence: str) -> str | None:
    """
    Collects and reassembles AIS fragments.
    Returns full payload when complete, otherwise None.
    """

    try:
        # !AIVDM,2,1,5,B,55NBJr02;FL@S@E>4p4@E=@E4p@E,0*3A
        parts = sentence.strip().split(",")

        total = int(parts[1])        # total number of fragments
        number = int(parts[2])       # fragment number
        seq_id = parts[3] or "NOSEQ"
        payload = parts[5]

        # Single sentence
        if total == 1:
            return payload

        # Multi-fragment sentence
        if seq_id not in _fragments:
            _fragments[seq_id] = {}

        _fragments[seq_id][number] = payload

        # Check if all fragments received
        if len(_fragments[seq_id]) == total:
            full_payload = "".join(
                _fragments[seq_id][i] for i in range(1, total + 1)
            )
            del _fragments[seq_id]
            return full_payload

        return None

    except Exception:
        return None
