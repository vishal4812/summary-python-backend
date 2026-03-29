from ..schemas import SummarizeRequest, SummarizeResponse


class DummySummarizer:
    def summarize(self, payload: SummarizeRequest) -> SummarizeResponse:
        bullet_points = [
            "This is a fixed dummy summary response from the local FastAPI backend.",
            "The endpoint contract is real, so the Flutter app can already integrate against it.",
            "Later, this service can be replaced with OpenAI or a self-hosted model without changing the app flow.",
        ]
        detailed = (
            "This is a fixed dummy summary response from the local FastAPI backend.\n\n"
            "Key points: " + " • ".join(bullet_points)
        )
        return SummarizeResponse(
            summary="This is a fixed dummy summary from the local FastAPI backend.",
            bulletPoints=bullet_points,
            detailedSummary=detailed,
        )
