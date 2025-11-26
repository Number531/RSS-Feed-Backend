# 🐛 MARGIN NOTES API DATA STRUCTURE MISMATCH

**Date:** November 24, 2025  
**Priority:** HIGH  
**Status:** BLOCKING FEATURE DEPLOYMENT  
**Affected Endpoint:** `GET /api/v1/articles/{id}/synthesis`

---

## 📋 Summary

The `margin_notes` array in the synthesis detail endpoint returns a data structure that does not match the frontend TypeScript interface, causing the margin notes feature to be non-functional.

---

## 🔍 Current Behavior (INCORRECT)

**API Response Structure:**
```json
{
  "article": {
    "margin_notes": [
      {
        "note": "Important context: This development builds on previous policy changes.",
        "location": "paragraph_2"
      },
      {
        "note": "Cross-reference: See related analysis in [Article XYZ]",
        "location": "paragraph_5"
      },
      {
        "note": "Expert perspective: Dr. Smith notes this is unprecedented.",
        "location": "paragraph_8"
      }
    ]
  }
}
```

### Issues:
1. ❌ Field named `location` (should be `paragraph_number`)
2. ❌ `location` is a **string** like `"paragraph_2"` (should be **integer** like `2`)
3. ❌ Missing required field `type` for categorization

---

## ✅ Expected Behavior (CORRECT)

**Required API Response Structure:**
```json
{
  "article": {
    "margin_notes": [
      {
        "note": "Important context: This development builds on previous policy changes.",
        "paragraph_number": 2,
        "type": "context"
      },
      {
        "note": "Cross-reference: See related analysis in [Article XYZ]",
        "paragraph_number": 5,
        "type": "evidence"
      },
      {
        "note": "Expert perspective: Dr. Smith notes this is unprecedented.",
        "paragraph_number": 8,
        "type": "clarification"
      }
    ]
  }
}
```

---

## 📝 Required Changes

### Change 1: Rename Field
```diff
- "location": "paragraph_2"
+ "paragraph_number": 2
```

### Change 2: Convert Type from String to Integer
```python
# Before (wrong):
"location": "paragraph_2"  # string

# After (correct):
"paragraph_number": 2  # integer
```

**Implementation:**
- If currently stored as `"paragraph_X"` format, extract the number:
  ```python
  # Example transformation
  location = "paragraph_2"
  paragraph_number = int(location.split("_")[1])  # Result: 2
  ```

### Change 3: Add Required `type` Field
```python
# Valid values (enum):
type: Literal["evidence", "context", "clarification"]
```

**Type Definitions:**
- `"evidence"` - Supporting facts, data, or documentation
- `"context"` - Background information or explanation
- `"clarification"` - Corrections or additional clarity

---

## 🎯 Frontend Contract

**TypeScript Interface the API MUST match:**
```typescript
interface MarginNote {
  paragraph_number: number;          // Integer, not string
  note: string;                      // Text content
  type: "evidence" | "context" | "clarification";  // Required enum
}
```

**Location in codebase:**
- File: `/frontend/types/api.ts`
- Lines: 373-378

---

## 🔧 Implementation Guidance

### Database Schema Check
Verify the `margin_notes` JSONB column structure in the articles table:
```sql
-- Check current structure
SELECT 
  id, 
  title,
  article_data->'margin_notes' as margin_notes
FROM articles 
WHERE has_synthesis = true
LIMIT 1;
```

### API Serialization Update
Update the synthesis detail endpoint response serializer:

**Location:** Likely in `app/api/v1/endpoints/articles.py` or similar

**Required Changes:**
1. Extract `margin_notes` from JSONB correctly
2. Transform `location` → `paragraph_number` (string → int)
3. Add `type` field (either from DB or assign default `"context"`)
4. Validate against enum: `["evidence", "context", "clarification"]`

### Example Backend Transformation:
```python
def transform_margin_notes(raw_notes: List[Dict]) -> List[Dict]:
    """Transform margin notes to match frontend contract."""
    transformed = []
    for note in raw_notes:
        # Extract paragraph number from location string
        location = note.get("location", "paragraph_0")
        if location.startswith("paragraph_"):
            paragraph_num = int(location.split("_")[1])
        else:
            paragraph_num = 0  # fallback
        
        transformed.append({
            "paragraph_number": paragraph_num,
            "note": note.get("note", ""),
            "type": note.get("type", "context")  # default to context if missing
        })
    
    return transformed
```

---

## 📊 Test Data

### Sample Correct Response
```json
{
  "article": {
    "id": "f16e1658-975a-470f-9dc8-44b9bd5cba8d",
    "title": "US-backed foreign broadcaster...",
    "margin_notes": [
      {
        "paragraph_number": 2,
        "note": "Important context: This development builds on previous policy changes.",
        "type": "context"
      },
      {
        "paragraph_number": 5,
        "note": "Cross-reference: See related analysis in [Article XYZ]",
        "type": "evidence"
      },
      {
        "paragraph_number": 8,
        "note": "Expert perspective: Dr. Smith notes this is unprecedented.",
        "type": "clarification"
      }
    ]
  }
}
```

---

## ✅ Acceptance Criteria

**The fix is complete when:**

1. ✅ API returns `paragraph_number` as an **integer** (not string)
2. ✅ API returns `type` field with valid enum value
3. ✅ Field is named `paragraph_number` (not `location`)
4. ✅ All existing margin notes data is migrated/transformed
5. ✅ Frontend component renders without TypeScript errors
6. ✅ Margin notes display correctly on synthesis detail page

---

## 🧪 Testing Instructions

### Test Endpoint:
```bash
curl http://localhost:8000/api/v1/articles/f16e1658-975a-470f-9dc8-44b9bd5cba8d/synthesis
```

### Verify Response Contains:
```json
"margin_notes": [
  {
    "paragraph_number": 2,  // ✅ integer
    "note": "...",          // ✅ string
    "type": "context"       // ✅ enum value
  }
]
```

### Validation Checklist:
- [ ] `paragraph_number` is type `int` (not `str`)
- [ ] `paragraph_number` is a positive integer (> 0)
- [ ] `type` is one of: `"evidence"`, `"context"`, `"clarification"`
- [ ] `note` is a non-empty string
- [ ] All three fields are present in every margin note object

---

## 🚨 Impact

**Without this fix:**
- ❌ Margin notes component cannot render (TypeScript type errors)
- ❌ Feature appears missing to users despite data existing
- ❌ Frontend crashes if component is used with current data structure
- ❌ Blocks deployment of synthesis mode feature

**With this fix:**
- ✅ Margin notes display correctly on synthesis detail pages
- ✅ Users can see contextual annotations
- ✅ Synthesis mode feature is complete and deployable

---

## 📞 Contact

**Reporter:** Frontend Team  
**Related Files:**
- Frontend: `/frontend/types/api.ts` (lines 373-378)
- Frontend: `/frontend/components/synthesis/margin-notes.tsx`
- Backend: Synthesis detail endpoint (needs update)

**Test Article ID:** `f16e1658-975a-470f-9dc8-44b9bd5cba8d`

---

## 📌 Related Issues

- ✅ References display working (fixed in commit `4be3180`)
- ✅ Timeline events display working
- ❌ **Margin notes display BLOCKED by this issue**

---

**END OF REPORT**
