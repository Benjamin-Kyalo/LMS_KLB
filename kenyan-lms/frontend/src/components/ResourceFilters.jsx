import FormField from "./FormField";

const TYPES = [
  ["PDF", "PDF"], ["VIDEO", "Video"], ["AUDIO", "Audio"],
  ["IMAGE", "Image"], ["INTERACTIVE", "Interactive"], ["LINK", "External link"],
];

function SelectFilter({ label, value, options, onChange, placeholder = "All" }) {
  return (
    <FormField label={label}>
      <select value={value || ""} onChange={(event) => onChange(event.target.value)}>
        <option value="">{placeholder}</option>
        {options.map((option) => (
          <option key={option.value} value={option.value}>{option.label}</option>
        ))}
      </select>
    </FormField>
  );
}

// Public and portal catalogues share the same filter contract. The API owns
// pagination and filtering; this component only collects query parameters.
export default function ResourceFilters({
  facets = {}, filters = {}, onFilter, query = "", onQuery, sort = "title", onSort,
}) {
  const levels = facets.levels || [];
  const selectedLevel = String(filters.level || "");
  const level = levels.find((item) => String(item.id) === selectedLevel);
  const areas = level?.learning_areas || facets.learning_areas || [];
  const collections = facets.collections || [];
  const subjects = facets.subjects || [];
  const classes = facets.classes || [];

  return (
    <form className="resource-filters panel panel-pad" onSubmit={(event) => event.preventDefault()}>
      <div className="resource-filter-grid">
        <FormField label="Search resources" full>
          <input
            type="search"
            value={query}
            placeholder="Title, description or keyword"
            onChange={(event) => onQuery(event.target.value)}
          />
        </FormField>
        <SelectFilter
          label="Level"
          value={filters.level}
          placeholder="All levels"
          options={levels.map((item) => ({ value: String(item.id), label: item.name }))}
          onChange={(value) => onFilter("level", value)}
        />
        <SelectFilter
          label="Learning area"
          value={filters.area}
          placeholder="All areas"
          options={areas.map((item) => ({ value: String(item.id), label: item.name }))}
          onChange={(value) => onFilter("area", value)}
        />
        <SelectFilter
          label="Collection"
          value={filters.collection}
          placeholder="All collections"
          options={collections.map((item) => ({ value: String(item.id), label: item.name }))}
          onChange={(value) => onFilter("collection", value)}
        />
        <SelectFilter
          label="Type"
          value={filters.resource_type}
          placeholder="All types"
          options={TYPES.map(([value, label]) => ({ value, label }))}
          onChange={(value) => onFilter("resource_type", value)}
        />
        <FormField label="Keyword">
          <input
            value={filters.keyword || ""}
            placeholder="e.g. fractions"
            onChange={(event) => onFilter("keyword", event.target.value)}
          />
        </FormField>
        {subjects.length > 0 && (
          <SelectFilter
            label="Subject"
            value={filters.subject}
            placeholder="All subjects"
            options={subjects.map((item) => ({ value: String(item.id), label: item.name }))}
            onChange={(value) => onFilter("subject", value)}
          />
        )}
        {classes.length > 0 && (
          <SelectFilter
            label="Class"
            value={filters.school_class}
            placeholder="All classes"
            options={classes.map((item) => ({
              value: String(item.id),
              label: [item.name, item.stream].filter(Boolean).join(" "),
            }))}
            onChange={(value) => onFilter("school_class", value)}
          />
        )}
        <SelectFilter
          label="Sort"
          value={sort}
          placeholder="Title"
          options={[
            { value: "title", label: "Title A–Z" },
            { value: "-published_at", label: "Newest first" },
            { value: "-size_kb", label: "Largest first" },
          ]}
          onChange={onSort}
        />
      </div>
    </form>
  );
}
