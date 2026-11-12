"""Nearest-centroid labels from the k=3 skill-rating fit."""

CENTROIDS = (
    (2.923076923076923, 3.0769230769230766, 2.8461538461538463, 4.0),
    (3.0, 3.6, 1.4, 1.6),
    (4.2, 4.6, 4.0, 4.6),
)


def predict_cluster(skills):
    """Return the index of the centroid closest to the four skill ratings."""
    best_label = 0
    best_distance = None
    for label, centroid in enumerate(CENTROIDS):
        distance = 0.0
        for rating, center in zip(skills, centroid):
            difference = rating - center
            distance += difference * difference
        if best_distance is None or distance < best_distance:
            best_distance = distance
            best_label = label
    return best_label
