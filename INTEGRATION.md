# Integrating the group model into the app

Instructions for an agent working in the app repo. The two model files are the source of truth. Do not edit them. The app adapts to their function signatures and to the import `from cluster_model import predict_cluster`.

## 1. What these two files do

`cluster_model.py` stores the three centroids from a k-means fit on the four skill ratings and returns the number of the nearest centroid. `assignment_rules.py` calls that function for every student, orders the clusters from most students to fewest, sorts each cluster by `id`, and deals the students to groups 1 through `n_groups`, continuing the count across clusters. The app loads students from Postgres and calls `assign_groups`; the CSV loader at the bottom of `assignment_rules.py` is not part of the app.

## 2. Files to copy

Copy these two files into the app repository root, the same directory as `app.py`:

- `cluster_model.py`
- `assignment_rules.py`

Leave them there as top-level modules. Do not move them into `backend/` and do not change their imports. `assignment_rules.py` imports `cluster_model` by that bare name, which resolves when both files sit on the application root and gunicorn runs with working directory `/app`.

Do not copy `fit_clusters.py`, `elbow.png`, or `class_dataset.csv`.

## 3. The two functions

`predict_cluster(skills)` takes the four ratings in this order: programming, data and stats, frontend design, business pitch. It returns the cluster number `0`, `1`, or `2`.

```python
predict_cluster((4, 5, 4, 5))  # 2
```

`assign_groups(students, n_groups=8)` takes a list of dicts. Each dict needs `id` and the four keys `skill_programming`, `skill_data_stats`, `skill_frontend_design`, and `skill_business_pitch`. It returns a list in the same order, each item holding `id`, `cluster`, and `group`. Group numbers start at 1. Equal-sized clusters are dealt in cluster-number order.

```python
assign_groups(
    [
        {"id": "a", "skill_programming": 4, "skill_data_stats": 5, "skill_frontend_design": 4, "skill_business_pitch": 5},
        {"id": "b", "skill_programming": 1, "skill_data_stats": 1, "skill_frontend_design": 1, "skill_business_pitch": 1},
        {"id": "c", "skill_programming": 3, "skill_data_stats": 4, "skill_frontend_design": 1, "skill_business_pitch": 2},
    ],
    n_groups=2,
)
# [
#   {"id": "a", "cluster": 2, "group": 1},
#   {"id": "b", "cluster": 1, "group": 1},
#   {"id": "c", "cluster": 1, "group": 2},
# ]
```

The real endpoint calls `assign_groups(students)` and keeps the default of 8 groups. Use each returned `cluster` only while building counts. Do not put it on a person in the JSON response.

## 4. Where the data comes from

The centroids were fit on `class_dataset.csv`. The running app reads Postgres. `schema.sql` defines the table. `deploy.py` loads that CSV into Postgres, and `docker/load_seed.py` loads `database/students.csv` for the local Docker database. Both scripts write the same `students` columns the model needs.

Read every student with the app's existing database helper, `backend.db.query`:

```sql
SELECT netid, name,
       skill_programming, skill_data_stats,
       skill_frontend_design, skill_business_pitch
FROM students
```

Pass this dict to `assign_groups`. `name` is not a model input. Keep it beside the call so the response can list names.

| Model input | Table.column | What differs from the CSV |
| --- | --- | --- |
| `id` | `students.netid` | Text, `NOT NULL`, unique. Both loaders store `netid.strip()`. Use this string as `id`. `students.student_id` is an identity integer generated on insert (`deploy.py` uses `RETURNING student_id`; `load_seed.py` inserts it with `OVERRIDING SYSTEM VALUE`). The current `/api/students` route returns `student_id`. The group model does not. Sorting is plain string order on `netid`. |
| `skill_programming` | `students.skill_programming` | CSV cells are text. The column is `INTEGER NOT NULL` and both loaders cast with `int()`. The check constraint is 1 through 5. Pass the integer through. The fit did not scale the ratings. |
| `skill_data_stats` | `students.skill_data_stats` | Same as programming. |
| `skill_frontend_design` | `students.skill_frontend_design` | Same as programming. |
| `skill_business_pitch` | `students.skill_business_pitch` | Same as programming. |

`students.name` (`TEXT NOT NULL`) is only for `members`. The schema says a name is not unique, so the list is display text. There is no `cluster` column and no `group` column. `deploy.py` does not load one. If a source CSV still has a `cluster` column from the fitting script, ignore it. Call `predict_cluster` through `assign_groups` instead.

Tools, availability, school year, and the other intake fields are not inputs.

## 5. Backend

Add `GET /api/groups` in `app.py`, next to the existing routes. Read every student with the query above. Build the dicts, call `assign_groups(students)`, and return one JSON object. On a database failure, use the same `api_error` path the other routes use.

```json
{
  "n_groups": 8,
  "groups": [
    {
      "group": 1,
      "members": ["First Person", "Second Person", "Third Person"],
      "cluster_counts": {"0": 2, "1": 1, "2": 0}
    }
  ],
  "clusters": [
    {
      "cluster": 0,
      "students": 13,
      "centroid": [2.923076923076923, 3.0769230769230766, 2.8461538461538463, 4.0]
    }
  ],
  "groups_missing_a_cluster": 6
}
```

- `n_groups` is the number passed into `assign_groups` (8).
- `groups` is ordered by group number, 1 through 8. `members` is the names of the students in that group and nothing else: no `netid`, no `student_id`, no `cluster`. `cluster_counts` maps every cluster number to how many members of the group came from it, including zeros.
- `clusters` is ordered by cluster number. `students` is the count of people in that cluster, not their names. `centroid` is the matching row of `cluster_model.CENTROIDS`, four numbers in the skill order programming, data and stats, frontend design, business pitch.
- `groups_missing_a_cluster` is how many groups have a zero in `cluster_counts`.

## 6. Frontend

Do not change `frontend/index.html`.

A later page can render `groups` as eight lists of names and show `cluster_counts` as the mix inside each group. `groups_missing_a_cluster` is the single summary number. `clusters` describes the three skill profiles: how many students fell into each, and the four centroid ratings in the order above. The payload never says which person belongs to which cluster. A group whose counts are `1, 1, 1` still does not identify which name is which cluster.

## 7. Packaging

No packaging file needs an edit.

`Dockerfile` already runs `COPY . .` into `/app` and starts `gunicorn app:app` with that working directory. `docker-compose.yml` builds the same image. `.dockerignore` does not exclude `*.py`. Leave `requirements.txt` as it is. These modules use the standard library only, so do not add scikit-learn, pandas, or matplotlib.

The two files have to be in the repo root that Docker copies, and they have to be committed. `.gitignore` ignores `class_dataset.csv`. The endpoint must not read that file. `deploy.py` loads the database; it does not ship the Python modules.

## 8. Test

Start the app the way the repo already does, so `DATABASE_URL` points at the seeded Postgres (`docker compose up`). Then:

```bash
curl -s http://127.0.0.1:8000/api/groups
```

Expect `n_groups` of 8, `groups_missing_a_cluster` of 6, and these sizes. Groups 1 through 7 have 3 members. Group 8 has 2. The cluster counts behind that result are:

| Group | Members | Cluster 0 | Cluster 1 | Cluster 2 |
| --- | --- | --- | --- | --- |
| 1 | 3 | 2 | 1 | 0 |
| 2 | 3 | 2 | 1 | 0 |
| 3 | 3 | 2 | 0 | 1 |
| 4 | 3 | 2 | 0 | 1 |
| 5 | 3 | 2 | 0 | 1 |
| 6 | 3 | 1 | 1 | 1 |
| 7 | 3 | 1 | 1 | 1 |
| 8 | 2 | 1 | 1 | 0 |

Cluster totals are 13, 5, and 5. Centroids are the three tuples in `cluster_model.py`. Groups 6 and 7 are the only groups that include every cluster.
