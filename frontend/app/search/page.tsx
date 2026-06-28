import { SearchForm } from "../../components/search/SearchForm";

export default function SearchDebugPage() {
  return (
    <div className="container mx-auto p-4 md:p-6 lg:p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight">Search Debug</h1>
        <p className="text-muted-foreground mt-2">
          Test retrieval strategies, tune chunking parameters, and inspect hybrid search scores without generating LLM responses.
        </p>
      </div>
      <SearchForm />
    </div>
  );
}
