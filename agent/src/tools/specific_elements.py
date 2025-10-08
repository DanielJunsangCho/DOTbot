def find_links(item):
    return item.find_all('a', href=True)

def find_table(child, logger, level):
    logger.info("------------------------------------THIS IS HAPPENING.---------------------------------------");
    rows = child.find_all('tr')
    content = []
    logger.debug(f"Found table with {len(rows)} rows")
    content.append(f"{'  ' * level}[TABLE]")
    for i, row in enumerate(rows):
        cells = row.find_all(['td', 'th'])
        if cells:
            row_text = " | ".join([cell.get_text().strip() for cell in cells])
            logger.info(row_text);
            if row_text.strip():
                logger.debug(f"Table row {i+1}: {len(cells)} cells")
                content.append(f"{'  ' * level}  {row_text}")
    return content