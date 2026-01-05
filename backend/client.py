import httpx

GRAPHQL_URL = "https://rickandmortyapi.com/graphql"

async def fetch_locations(page: int = 1):
    query = """
    query ($page: Int) {
      locations(page: $page) {
        results {
          id
          name
          type
          dimension
          residents {
            id
            name
            status
            species
            image
          }
        }
      }
    }
    """
    variables = {"page": page}
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(GRAPHQL_URL, json={"query": query, "variables": variables})
            if response.status_code == 200:
                data = response.json()
                return data.get("data", {}).get("locations", {}).get("results", [])
            return []
        except Exception as e:
            print(f"Error fetching locations: {e}")
            return []

async def fetch_characters_by_ids(ids: list[str]):
    if not ids:
        return []
    
    query = """
    query ($ids: [ID!]!) {
      charactersByIds(ids: $ids) {
        id
        name
        status
        species
        type
        gender
        image
        origin {
            name
        }
        location {
            name
        }
      }
    }
    """
    variables = {"ids": ids}
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(GRAPHQL_URL, json={"query": query, "variables": variables})
            if response.status_code == 200:
                data = response.json()
                return data.get("data", {}).get("charactersByIds", [])
            return []
        except Exception as e:
            print(f"Error fetching characters: {e}")
            return []

async def fetch_locations_by_ids(ids: list[str]):
    if not ids:
        return []

    query = """
    query ($ids: [ID!]!) {
      locationsByIds(ids: $ids) {
        id
        name
        type
        dimension
        residents {
            id
            name
            status
            species
            image
        }
      }
    }
    """
    variables = {"ids": ids}
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(GRAPHQL_URL, json={"query": query, "variables": variables})
            if response.status_code == 200:
                data = response.json()
                return data.get("data", {}).get("locationsByIds", [])
            return []
        except Exception as e:
            print(f"Error fetching locations: {e}")
            return []
