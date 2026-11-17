# Source hierarchy and revision control

## Authority order

1. The project's authorized copy of the exact UCIe specification revision.
2. Applicable official UCIe ECNs, errata, addenda, and consortium clarifications.
3. Official UCIe Consortium publications and implementation guidance.
4. Relevant Accellera standards and approved verification methodology references.
5. Peer-reviewed papers and conference publications.
6. Vendor application notes, technical briefs, and product documentation.
7. Open-source implementations, forums, blogs, and informal discussions.

Lower-level sources can provide context or implementation examples. They do not override normative specifications.

## Source register fields

For every controlled source, record:
- Unique source ID.
- Full title and issuing organization.
- Revision/version and publication date.
- Exact file name or official URL.
- Access/licensing status.
- Local file hash when applicable.
- Sections used by each requirement.
- Date checked and reviewer.

## Revision policy

- Freeze one baseline for each design configuration.
- Record every ECN or clarification applied.
- Never silently combine requirements from different revisions.
- For migration, produce a delta matrix: changed requirement, affected RTL, affected tests, affected constraints, and required re-verification.
- Mark unavailable or unverified material explicitly.

## Citation format

Use a reproducible citation such as: document title, revision, clause/subclause, table/figure, page, and controlled source ID. Do not invent a clause number or page. If a page number is not available, omit it and state why.

## Copyright and confidentiality

Do not copy substantial specification text into generated documentation or public repositories. Store only authorized source references and original paraphrases. Do not upload proprietary project files or licensed standards to public services without permission.
