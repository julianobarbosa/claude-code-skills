# Obsidian Canvas Reference

Canvas is a visual tool for spatially organizing notes, images, and other content.

## File Format

Canvas files use `.canvas` extension and store JSON data:

```json
{
  "nodes": [],
  "edges": []
}
```

## Node Types

### Text Node

```json
{
  "id": "unique-id",
  "type": "text",
  "x": 0,
  "y": 0,
  "width": 250,
  "height": 100,
  "text": "Your text content here"
}
```

### File Node (Embed Note)

```json
{
  "id": "unique-id",
  "type": "file",
  "file": "path/to/note.md",
  "x": 300,
  "y": 0,
  "width": 400,
  "height": 300
}
```

### Link Node (Web Embed)

```json
{
  "id": "unique-id",
  "type": "link",
  "url": "https://example.com",
  "x": 0,
  "y": 200,
  "width": 400,
  "height": 300
}
```

### Group Node

```json
{
  "id": "unique-id",
  "type": "group",
  "x": -50,
  "y": -50,
  "width": 600,
  "height": 400,
  "label": "Group Name"
}
```

## Edges (Connections)

```json
{
  "id": "edge-id",
  "fromNode": "source-node-id",
  "fromSide": "right",
  "toNode": "target-node-id",
  "toSide": "left",
  "color": "1",
  "label": "Connection label"
}
```

### Side Options

- `top`
- `right`
- `bottom`
- `left`

### Color Options

Canvas uses numbered colors 1-6:
- 1: Red
- 2: Orange
- 3: Yellow
- 4: Green
- 5: Cyan
- 6: Purple

## Node Colors

Add `color` property to any node:

```json
{
  "id": "node-id",
  "type": "text",
  "color": "1",
  "text": "Red text card"
}
```

## Complete Canvas Example

```json
{
  "nodes": [
    {
      "id": "1",
      "type": "text",
      "x": 0,
      "y": 0,
      "width": 200,
      "height": 100,
      "text": "# Main Idea\n\nCore concept description"
    },
    {
      "id": "2",
      "type": "file",
      "file": "04 - Permanent/concept-note.md",
      "x": 300,
      "y": 0,
      "width": 300,
      "height": 200
    },
    {
      "id": "3",
      "type": "text",
      "x": 0,
      "y": 150,
      "width": 200,
      "height": 80,
      "text": "Related thought",
      "color": "4"
    },
    {
      "id": "group1",
      "type": "group",
      "x": -20,
      "y": -20,
      "width": 640,
      "height": 280,
      "label": "Knowledge Cluster"
    }
  ],
  "edges": [
    {
      "id": "e1",
      "fromNode": "1",
      "fromSide": "right",
      "toNode": "2",
      "toSide": "left",
      "label": "expands on"
    },
    {
      "id": "e2",
      "fromNode": "1",
      "fromSide": "bottom",
      "toNode": "3",
      "toSide": "top",
      "color": "4"
    }
  ]
}
```

## Creating Canvas Programmatically

### Basic Structure

```python
import json

canvas = {
    "nodes": [],
    "edges": []
}

# Add nodes
canvas["nodes"].append({
    "id": "node1",
    "type": "text",
    "x": 0,
    "y": 0,
    "width": 250,
    "height": 100,
    "text": "Content here"
})

# Save
with open("my-canvas.canvas", "w") as f:
    json.dump(canvas, f, indent=2)
```

### Grid Layout Helper

```python
def create_grid_canvas(items, cols=3, card_width=250, card_height=100, gap=50):
    nodes = []
    for i, item in enumerate(items):
        row = i // cols
        col = i % cols
        nodes.append({
            "id": f"node-{i}",
            "type": "text",
            "x": col * (card_width + gap),
            "y": row * (card_height + gap),
            "width": card_width,
            "height": card_height,
            "text": item
        })
    return {"nodes": nodes, "edges": []}
```

## Best Practices

1. **Use groups** to organize related nodes
2. **Color-code** by category or status
3. **Keep text concise** in text nodes
4. **Embed notes** for detailed content
5. **Label edges** for relationship clarity
6. **Maintain spacing** for readability

## Canvas Use Cases

- **Mind mapping**: Brainstorm and connect ideas
- **Project planning**: Visual task boards
- **Knowledge graphs**: Visualize note relationships
- **Mood boards**: Collect visual inspiration
- **Architecture diagrams**: System design
- **Flowcharts**: Process documentation
