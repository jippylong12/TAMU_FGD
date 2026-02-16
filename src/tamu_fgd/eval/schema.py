PAGE_RECORDS_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "records": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "record_type": {
                        "type": "string",
                        "enum": ["section", "course_total", "department_total"],
                    },
                    "record_id": {"type": "string"},
                    "counts": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "a": {"type": "integer"},
                            "b": {"type": "integer"},
                            "c": {"type": "integer"},
                            "d": {"type": "integer"},
                            "f": {"type": "integer"},
                            "af_total": {"type": "integer"},
                            "i": {"type": "integer"},
                            "s": {"type": "integer"},
                            "u": {"type": "integer"},
                            "q": {"type": "integer"},
                            "x": {"type": "integer"},
                            "isuqx_total": {"type": "integer"},
                        },
                        "required": [
                            "a",
                            "b",
                            "c",
                            "d",
                            "f",
                            "af_total",
                            "i",
                            "s",
                            "u",
                            "q",
                            "x",
                            "isuqx_total",
                        ],
                    },
                    "gpa": {"type": "number"},
                    "instructor": {"type": ["string", "null"]},
                },
                "required": ["record_type", "record_id", "counts", "gpa", "instructor"],
            },
        }
    },
    "required": ["records"],
}


def empty_counts() -> dict:
    return {
        "a": 0,
        "b": 0,
        "c": 0,
        "d": 0,
        "f": 0,
        "af_total": 0,
        "i": 0,
        "s": 0,
        "u": 0,
        "q": 0,
        "x": 0,
        "isuqx_total": 0,
    }
