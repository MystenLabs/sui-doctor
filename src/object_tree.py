import json


PRIMITIVE_TYPES = (str, int, float, bool)
COLLECTION_TYPES = (list, set, tuple)
MAP_TYPES = (dict,)


def hack_load(val):
  pre_wrapper = {"val": str(val)}
  print(json.dumps(pre_wrapper))
  post_wrapper = json.loads(json.dumps(pre_wrapper))
  return post_wrapper['val']


def get_object_graph(obj, visited=None):
    """
    Recursively traverses the object graph/tree of an object and returns a JSON-serializable representation.

    Args:
        obj: The object to traverse.
        visited (set): A set to track visited objects and detect cycles. (default: None)

    Returns:
        JSON-serializable representation of the object graph/tree.
    """
    if visited is None:
        visited = set()

    if id(obj) in visited:
        return hack_load(obj)

    visited.add(id(obj))

    if isinstance(obj, COLLECTION_TYPES):
        return [get_object_graph(item, visited) for item in obj]
    elif isinstance(obj, MAP_TYPES):
        return {str(key): get_object_graph(value, visited) for key, value in obj.items()}
    elif hasattr(obj, '__dict__'):  # Custom object type
        return {key: get_object_graph(value, visited) for key, value in vars(obj).items() if not callable(value)}
    else:
        return hack_load(obj)


def object_to_json(obj):
    """
    Serializes an object to JSON.

    Args:
        obj: The object to serialize.

    Returns:
        A JSON string representing the object.
    """
    graph = get_object_graph(obj)
    return json.dumps(graph, indent=4)
