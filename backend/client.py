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
