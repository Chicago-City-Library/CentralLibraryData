import pandas as pd
import ast

# STEP 1: Load the data we need from each file
# only keep the columns Java's DVD class actually needs
metadata = pd.read_csv("movies_metadata.csv", low_memory=False)
metadata = metadata[["id", "title", "genres", "runtime"]]

credits = pd.read_csv("credits.csv")

# only load the 2 columns we need from ratings.csv
ratings = pd.read_csv("ratings.csv", usecols=["movieId", "rating"])

# STEP 2: Clean up movies_metadata
#drop corrupted non-numeric id rows
metadata = metadata[metadata["id"].apply(lambda x: str(x).isdigit())]
metadata["id"] = metadata["id"].astype(int)

# just get names from the 'genres' string column
# join names together: "Animation, Comedy"
def genre_names(genre_string):
    try: genre_list = ast.literal_eval(genre_string)
    except Exception: genre_list = []
    names = [g["name"] for g in genre_list]
    return ", ".join(names) if names else "Unknown"

metadata["genre"] = metadata["genres"].apply(genre_names)
metadata = metadata.drop(columns=["genres"])

# STEP 3: Pull the director's name out of credits.csv
# dont need gender, credit_id, department, or profile_path in string of dictionaries, only pull out name of job == director
def get_director(crew_string):
    try: crew_list = ast.literal_eval(crew_string)
    except Exception: crew_list = []
    directors = [p.get("name", "Unknown") for p in crew_list if p.get("job") == "Director"]
    return directors[0] if directors else "Unknown"

credits["director"] = credits["crew"].apply(get_director)
credits = credits[["id", "director"]]

# STEP 4: Turn thousands of individual user ratings into one average rating per movie
avg_ratings = ratings.groupby("movieId")["rating"].mean().round(1).reset_index()
avg_ratings = avg_ratings.rename(columns={"movieId": "id", "rating": "rating"})

# STEP 5: Combine everything into one table, connected by movie id
combined = metadata.merge(credits, on="id", how="left")
combined = combined.merge(avg_ratings, on="id", how="left")

# Fill in missing values with defaults not blanks
combined["director"] = combined["director"].fillna("Unknown")
combined["rating"] = combined["rating"].fillna("na")
combined["runtime"] = combined["runtime"].fillna(0)

# STEP 6: Rename 'runtime' to 'minutes' to match Java's DVD field name
combined = combined.rename(columns={"runtime": "minutes"})
final_data = combined[["id", "title", "director", "minutes", "rating", "genre"]]

# STEP 7: Export one combined JSON file for the Java team
final_data.to_json("aggregated_movies.json", orient="records", indent=2)

print(f"Done! Combined {len(final_data)} movies into aggregated_movies.json")