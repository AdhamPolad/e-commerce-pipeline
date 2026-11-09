# Presentation outline (8–10 slides)
1. **Title + team** – names, roles, GitHub link
2. **Goal & architecture** – the pipeline diagram from the README
3. **Data source** – DummyJSON API, fields kept, sample Parquet rows (`df.head()`)
4. **Sales data** – how it was generated; show 5 dirty rows
5. **Cleaning steps** – the rules table + the printed cleaning report (rows in → out, rejected by reason)
6. **Data model** – ER diagram, PKs/FKs, why `unit_price` is on `order_items`
7. **Loading** – parents before children, idempotent upserts, row counts per table
8. **Results** – total sales value by product (query + result table, optional chart)
9. **Teamwork** – branches, PRs, review comments screenshots
10. **Lessons learned / next steps**
