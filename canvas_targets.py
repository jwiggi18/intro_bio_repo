"""
canvas_targets.py — non-secret per-course configuration for the multi-course
BIOL 1113 build.

This repo now feeds more than one Canvas course: the "sandbox" (the
template course other instructors will import to teach the course), any
"live" course(s) taught directly from this repo before the sandbox is fully
built out, or in future semesters, and the "hybrid" course (lecture + GTA-led
small group, no blog posts/comments — its content genuinely differs from
sandbox/live, not just its Canvas ids; see content_root below). Only a
handful of course-specific values differ per target, listed below.

Safe to commit -- no credentials live here. The Canvas API token stays in
.env (gitignored) and is looked up separately by upload_to_canvas.py.

Each target needs:
  - course_id: the Canvas course ID. None means "not set up yet" -- build
    and upload scripts will refuse to run against a target with no id.
  - base_url: the Canvas instance (kept per-target in case that's ever not
    the same across courses; today it always is).
  - content_root: where this target's source HTML lives, relative to the
    repo root. Omit (or use ".") for the default — root-level *.html plus
    week01-week15/week.html, the layout sandbox/live share. Set to a
    subfolder name (e.g. "hybrid") when a target's content is genuinely
    different, not just a different Canvas id — that subfolder must mirror
    the same layout (homepage.html, syllabus.html, weekNN/week.html).
  - learning_notes_ids: that course's own Learning Notes assignment ids,
    one per week (1-15). These are NOT shared across courses -- Canvas
    assigns a fresh id to every assignment in every course, even when it
    was copied from another course via import. Run
    `python3 scripts/create_learning_notes_group.py <target>` to create
    its Learning Notes assignments, then paste the resulting ids in here.
  - small_group_ids: same idea as learning_notes_ids, but for the "Small
    Group Participation" assignment group (hybrid course only — sandbox/live
    don't have this category, so they omit the key entirely). Run
    `python3 scripts/create_small_group_group.py <target>` to create its
    Small Group Participation assignments, then paste the resulting ids in
    here.
  - blog_post_ids / blog_comment_ids: same idea, for "Week N Blog Post" and
    "Week N Blog Comment Declaration" (weeks 2-15 only — live+sandbox only,
    hybrid doesn't have these). These assignments were created directly in
    Canvas (not via a repo script) before this key existed; ids captured via
    the Canvas API Aug 16, 2026. If a future semester's course needs these
    created fresh, create the "Blog Posts" / "Blog Comments" assignment
    groups (drop_lowest=4 each, matching the existing courses) and their 14
    weekly assignments by hand or with a new script mirroring
    create_learning_notes_group.py, then paste the resulting ids in here.
  - slides_urls: that course's own hosted copies of the video-slide PDFs
    (scripts/extract_video_slides.py output), keyed by the source video's
    filename stem (e.g. "Cholera_intro" for Cholera_intro.mp4 /
    Cholera_intro.pdf). Also NOT shared across courses. Referenced from week
    pages via {{SLIDES_URL:<key>}} — a key missing from this dict leaves
    that one placeholder unresolved rather than breaking the whole page. Run
    scripts/upload_slides_to_canvas.py against a course to upload the full
    video_slides/ set, then paste the resulting dict in here.
  - syllabus_pdf_url: that course's own hosted copy of the static syllabus
    PDF (BIOL1113_Syllabus_Fall2026.pdf) — live+sandbox only (hybrid has its
    own separate syllabus.html, no PDF download link requested for it). Run
    scripts/upload_syllabus_pdf_to_canvas.py against a course to upload it,
    then paste the resulting URL in here.
  - chart_image_url: that course's own hosted copy of the syllabus grade
    donut chart PNG. Also NOT shared across courses -- Canvas files belong
    to one course each. None means "not uploaded to this course yet" --
    the syllabus build will leave {{CHART_IMAGE_URL}} unresolved (visibly
    broken) until this is filled in. Run
    scripts/upload_chart_to_canvas.py against a course to upload it, then
    paste the resulting URL in here.

To add a new target (a new semester's section, another instructor's course,
etc.): copy one of the blocks below, fill in the course_id, run
`create_learning_notes_group.py <target>` (and `create_small_group_group.py
<target>`, for hybrid) and `upload_chart_to_canvas.py <target>` against it,
and fill in the resulting ids / chart_image_url. Nothing else in the repo
needs to change -- every script here takes the target name as its first
argument.
"""

TARGETS = {
    "sandbox": {
        "course_id": "215536",
        "base_url": "https://canvas.okstate.edu",
        "learning_notes_ids": {
            1: 2673768, 2: 2673769, 3: 2673770, 4: 2673771, 5: 2673772,
            6: 2673773, 7: 2673774, 8: 2673775, 9: 2673776, 10: 2673777,
            11: 2673778, 12: 2673779, 13: 2673780, 14: 2673781, 15: 2673782,
        },
        # Weeks 2-15 only (matches Jodie's Aug 16, 2026 request scope).
        # Captured via Canvas API from assignments already created directly
        # in Canvas, in the "Blog Posts" (group 484895) / "Blog Comments"
        # (group 484896) groups. A separate, older-naming duplicate set
        # ("Blog Comment Declaration — Week 02" etc., ids 2638566-2638579,
        # sitting in the default "Assignments" group) also exists in this
        # course and looks like leftover cruft from an earlier setup pass —
        # left alone/unlinked here, flagged for Jodie to clean up or delete.
        "blog_post_ids": {
            2: 2696355, 3: 2696357, 4: 2696358, 5: 2696359, 6: 2696361,
            7: 2696364, 8: 2696368, 9: 2696370, 10: 2696371, 11: 2696372,
            12: 2696373, 13: 2696374, 14: 2696375, 15: 2696376,
        },
        "blog_comment_ids": {
            2: 2696381, 3: 2696384, 4: 2696388, 5: 2696389, 6: 2696391,
            7: 2696394, 8: 2696397, 9: 2696399, 10: 2696404, 11: 2696410,
            12: 2696415, 13: 2696422, 14: 2696428, 15: 2696434,
        },
        "slides_urls": {
            "Course_Overview_Syllabus": "https://canvas.okstate.edu/files/26570546/download?download_frd=1&verifier=dfe5b4e6-8fd0-46a2-8706-ab9ce329ae57",
            "Instructor_Intro": "https://canvas.okstate.edu/files/26570547/download?download_frd=1&verifier=3705c84f-3c90-42ff-aa4c-a69e2376ef59",
            "What-is-biology": "https://canvas.okstate.edu/files/26570550/download?download_frd=1&verifier=15c136dd-eff9-47e7-b466-c9e8bfbf8b0a",
            "Science_and_Peer_Review": "https://canvas.okstate.edu/files/26570548/download?download_frd=1&verifier=f3a8e8e7-b34a-4f22-999e-9d409bc74891",
            "Cholera_intro": "https://canvas.okstate.edu/files/26570545/download?download_frd=1&verifier=7f10f6e7-151e-46c0-94d5-57e1ecb6dbc4",
            "The_cell_intro": "https://canvas.okstate.edu/files/26570549/download?download_frd=1&verifier=875eed99-855b-4896-b979-6e34116f9abb",
            "Cell_Membrane_Passive_Transport": "https://canvas.okstate.edu/files/26570542/download?download_frd=1&verifier=9a2ed79a-14ac-4d97-afca-a5166d128d18",
            "Cell_membrane_active_transport": "https://canvas.okstate.edu/files/26570543/download?download_frd=1&verifier=4dda8ff0-b4e5-4868-8048-4db73a7e901e",
            "Cholera_explained": "https://canvas.okstate.edu/files/26570544/download?download_frd=1&verifier=d62d85f4-ba47-4f2c-af13-063de7c53306",
        },
        "syllabus_pdf_url": "https://canvas.okstate.edu/files/26570571/download?download_frd=1&verifier=f584d376-9267-40c4-a3f6-f401e1d49ca9",
        "chart_image_url": "https://canvas.okstate.edu/files/26482456/download?download_frd=1&verifier=o5RBhzPh7ATKKQ21Nv2txPsoFmEhjTW3mzmDRv3Q",
        "multipage_pdf_url": "https://canvas.okstate.edu/files/26569303/download?download_frd=1&verifier=6c716755-702c-4a68-a239-f3a39222322f",
        # Weeks 1-2 guided Learning Notes .docx handouts, uploaded Aug 17,
        # 2026 via scripts/upload_learning_notes_to_canvas.py. Keys match
        # slides_urls stems where a slide deck also exists for that video.
        "notes_urls": {
            "Course_Overview_Syllabus": "https://canvas.okstate.edu/files/26595463/download?download_frd=1&verifier=fd3a9620-71e1-4599-a80e-39fcc70c45cd",
            "Instructor_Intro": "https://canvas.okstate.edu/files/26595465/download?download_frd=1&verifier=2c9107d7-f810-4fe2-b584-d72f0cf97caa",
            "Neuroscience_of_Learning": "https://canvas.okstate.edu/files/26595466/download?download_frd=1&verifier=1b833a3c-fea6-4339-98b1-3daa622e70f7",
            "How_to_Study_Effectively": "https://canvas.okstate.edu/files/26595467/download?download_frd=1&verifier=da068b99-573d-4505-bdd3-d711a37a0881",
            "What-is-biology": "https://canvas.okstate.edu/files/26595468/download?download_frd=1&verifier=e10aaca2-9b30-48f5-88ea-c5fa824ecd8c",
            "Science_and_Peer_Review": "https://canvas.okstate.edu/files/26595469/download?download_frd=1&verifier=1b76bfd5-2aa0-4197-9c32-3a719f7a3cce",
            "The_cell_intro": "https://canvas.okstate.edu/files/26595470/download?download_frd=1&verifier=eafc5442-2c7d-44e9-8f36-a4f76fe7feec",
            "Cholera_intro": "https://canvas.okstate.edu/files/26595471/download?download_frd=1&verifier=9ca7970a-3736-4796-908a-424ac69953ab",
            "Cell_Membrane_Passive_Transport": "https://canvas.okstate.edu/files/26595473/download?download_frd=1&verifier=1ccf0adb-bb1b-4ca9-b249-d1607040c712",
            "Cell_membrane_active_transport": "https://canvas.okstate.edu/files/26659335/download?download_frd=1&verifier=6ea77d50-6f8e-4ca0-b5af-7f500a480893",
            "Cholera_explained": "https://canvas.okstate.edu/files/26595475/download?download_frd=1&verifier=9ef76bd6-a48c-40d0-b86d-55e8a625c054",
        },
    },

    "live": {
        "course_id": "238411",
        "base_url": "https://canvas.okstate.edu",
        "learning_notes_ids": {
            1: 2678256, 2: 2678257, 3: 2678258, 4: 2678259, 5: 2678260,
            6: 2678261, 7: 2678262, 8: 2678263, 9: 2678264, 10: 2678265,
            11: 2678266, 12: 2678267, 13: 2678268, 14: 2678269, 15: 2678270,
        },
        # Weeks 2-15 only (matches Jodie's Aug 16, 2026 request scope). A
        # "Week 1 Blog Post" (id 2696672, 0 pts, published) also exists in
        # this course -- looks like a vestigial/practice item from an
        # earlier setup pass, out of scope for this request, left as-is.
        "blog_post_ids": {
            2: 2696449, 3: 2696450, 4: 2696451, 5: 2696452, 6: 2696455,
            7: 2696459, 8: 2696465, 9: 2696471, 10: 2696478, 11: 2696480,
            12: 2696481, 13: 2696482, 14: 2696483, 15: 2696484,
        },
        "blog_comment_ids": {
            2: 2696485, 3: 2696486, 4: 2696487, 5: 2696488, 6: 2696489,
            7: 2696490, 8: 2696491, 9: 2696492, 10: 2696493, 11: 2696494,
            12: 2696495, 13: 2696496, 14: 2696497, 15: 2696498,
        },
        "slides_urls": {
            "Course_Overview_Syllabus": "https://canvas.okstate.edu/files/26570556/download?download_frd=1&verifier=db8df6ca-b2d9-4719-93e6-6fb8ec1447ec",
            "Instructor_Intro": "https://canvas.okstate.edu/files/26570557/download?download_frd=1&verifier=99ee086b-25e4-4b63-a20b-d5440f281a5c",
            "What-is-biology": "https://canvas.okstate.edu/files/26570560/download?download_frd=1&verifier=b3116d5f-2b45-4a31-8f12-6673ae70844c",
            "Science_and_Peer_Review": "https://canvas.okstate.edu/files/26570558/download?download_frd=1&verifier=87159f34-8b23-476f-8f3e-d1b666810d0a",
            "Cholera_intro": "https://canvas.okstate.edu/files/26570555/download?download_frd=1&verifier=2c4022de-26f2-469e-a5c0-aca79ae0f00d",
            "The_cell_intro": "https://canvas.okstate.edu/files/26570559/download?download_frd=1&verifier=c6e970c4-4c95-4f52-8b1f-0bfd0cf5730c",
            "Cell_Membrane_Passive_Transport": "https://canvas.okstate.edu/files/26570551/download?download_frd=1&verifier=6f08f24e-6851-4b18-a4d5-243d23e11bf6",
            "Cell_membrane_active_transport": "https://canvas.okstate.edu/files/26570552/download?download_frd=1&verifier=2c06b91d-3246-40a6-9d99-3e8a6a6bf51f",
            "Cholera_explained": "https://canvas.okstate.edu/files/26570554/download?download_frd=1&verifier=3c14fe89-6c24-4508-8898-a8b6c516bcae",
        },
        "syllabus_pdf_url": "https://canvas.okstate.edu/files/26570572/download?download_frd=1&verifier=8a514192-b6a2-4ccd-b4de-27a6d4b36b91",
        "chart_image_url": "https://canvas.okstate.edu/files/26482457/download?download_frd=1&verifier=NQHKoLhs2nukRk0uc3VtzXzsAJ39FvB1N3FG5trv",
        "multipage_pdf_url": "https://canvas.okstate.edu/files/26569325/download?download_frd=1&verifier=8b319392-2680-45cc-9cd6-31796bc5f47a",
        # Weeks 1-2 guided Learning Notes .docx handouts, uploaded Aug 17,
        # 2026 via scripts/upload_learning_notes_to_canvas.py. Keys match
        # slides_urls stems where a slide deck also exists for that video.
        "notes_urls": {
            "Course_Overview_Syllabus": "https://canvas.okstate.edu/files/26595476/download?download_frd=1&verifier=1ad3031c-1a43-4141-96f0-eb66b42a80b8",
            "Instructor_Intro": "https://canvas.okstate.edu/files/26595477/download?download_frd=1&verifier=52727fc4-f948-40e4-9976-bd33e3e60b13",
            "Neuroscience_of_Learning": "https://canvas.okstate.edu/files/26595478/download?download_frd=1&verifier=2aa69f4e-16bb-4da9-9e3e-bbe7f61cb9bc",
            "How_to_Study_Effectively": "https://canvas.okstate.edu/files/26595479/download?download_frd=1&verifier=d218c1ee-5104-4658-bbf5-4ff80102c049",
            "What-is-biology": "https://canvas.okstate.edu/files/26595480/download?download_frd=1&verifier=fe8971bd-6bb5-4d4c-a8c2-558e2af5d46e",
            "Science_and_Peer_Review": "https://canvas.okstate.edu/files/26595481/download?download_frd=1&verifier=e01afd95-b4bb-4380-9423-10be379ab768",
            "The_cell_intro": "https://canvas.okstate.edu/files/26595486/download?download_frd=1&verifier=4add353d-0cab-4049-81c0-68ddc4cf1e65",
            "Cholera_intro": "https://canvas.okstate.edu/files/26595487/download?download_frd=1&verifier=fc55adff-d499-48a6-8d0e-c3c9d22d3926",
            "Cell_Membrane_Passive_Transport": "https://canvas.okstate.edu/files/26595488/download?download_frd=1&verifier=53637a1a-c00a-4342-b2a0-2c565889dcde",
            "Cell_membrane_active_transport": "https://canvas.okstate.edu/files/26659337/download?download_frd=1&verifier=4605a780-7e27-4a34-a520-73aeffa91428",
            "Cholera_explained": "https://canvas.okstate.edu/files/26595490/download?download_frd=1&verifier=62ea6d14-75cc-40fb-b9aa-add5aab9f97f",
        },
    },

    # Hybrid: lecture (Mon, NRC 106, 3:30-4:20) + GTA-led small group
    # (Claudia Goss) replacing Blog Posts/Blog Comments. Content genuinely
    # differs from sandbox/live (first video slot each week becomes a
    # lecture notice, no blog assignment links, Small Group Participation
    # link instead) — see content_root and hybrid/ in the repo. Course id
    # 239593 confirmed by Jodie Aug 13, 2026. learning_notes_ids and
    # learning_notes_ids and small_group_ids populated Aug 13, 2026 by running
    #   python3 scripts/create_learning_notes_group.py hybrid
    #   python3 scripts/create_small_group_group.py hybrid
    # against course 239593. All 30 assignments created as unpublished drafts.
    "hybrid": {
        "course_id": "239593",
        "base_url": "https://canvas.okstate.edu",
        "content_root": "hybrid",
        "learning_notes_ids": {
            1: 2690603, 2: 2690604, 3: 2690605, 4: 2690606, 5: 2690607,
            6: 2690608, 7: 2690609, 8: 2690610, 9: 2690611, 10: 2690612,
            11: 2690613, 12: 2690614, 13: 2690615, 14: 2690616, 15: 2690617,
        },
        "small_group_ids": {
            1: 2690618, 2: 2690619, 3: 2690620, 4: 2690621, 5: 2690622,
            6: 2690623, 7: 2690624, 8: 2690625, 9: 2690626, 10: 2690627,
            11: 2690628, 12: 2690629, 13: 2690630, 14: 2690631, 15: 2690632,
        },
        "slides_urls": {
            "Course_Overview_Syllabus": "https://canvas.okstate.edu/files/26570566/download?download_frd=1&verifier=e7b47bd0-c709-4d67-a90c-4af452c52b2b",
            "Instructor_Intro": "https://canvas.okstate.edu/files/26570567/download?download_frd=1&verifier=98bc831f-0781-437b-bf84-ac9ad8e444a1",
            "What-is-biology": "https://canvas.okstate.edu/files/26570570/download?download_frd=1&verifier=3c33e86d-9444-40ad-9895-99ca2300a13a",
            "Science_and_Peer_Review": "https://canvas.okstate.edu/files/26570568/download?download_frd=1&verifier=a5eca2e5-d36a-4982-b2ae-c099c3aa16d2",
            "Cholera_intro": "https://canvas.okstate.edu/files/26570565/download?download_frd=1&verifier=5b3dd56e-2626-415a-96e8-833d1f339561",
            "The_cell_intro": "https://canvas.okstate.edu/files/26570569/download?download_frd=1&verifier=ec84a9c2-6c93-4b8d-ae81-ac633bf9eaac",
            "Cell_Membrane_Passive_Transport": "https://canvas.okstate.edu/files/26570561/download?download_frd=1&verifier=2ee792bf-6d91-4c39-8809-96fe1dc9f6eb",
            "Cell_membrane_active_transport": "https://canvas.okstate.edu/files/26570563/download?download_frd=1&verifier=61dc3707-9e5a-40c3-89c3-6daff57c557f",
            "Cholera_explained": "https://canvas.okstate.edu/files/26570564/download?download_frd=1&verifier=e321770f-d7a0-4766-8b26-05453fdf3e18",
        },
        "chart_image_url": "https://canvas.okstate.edu/files/26527152/download?download_frd=1&verifier=51e6d4b4-6b92-42f5-b66d-ebe796210997",
        "multipage_pdf_url": "https://canvas.okstate.edu/files/26569344/download?download_frd=1&verifier=00db8885-27f0-42ba-a79c-84039e52cd99",
        # Weeks 1-2 guided Learning Notes .docx handouts, uploaded Aug 17,
        # 2026 via scripts/upload_learning_notes_to_canvas.py. Keys match
        # slides_urls stems where a slide deck also exists for that video.
        "notes_urls": {
            "Course_Overview_Syllabus": "https://canvas.okstate.edu/files/26595491/download?download_frd=1&verifier=87c53bc5-2d9b-40fa-9020-cc5595af4134",
            "Instructor_Intro": "https://canvas.okstate.edu/files/26595493/download?download_frd=1&verifier=bd55baff-fe0b-4865-85d0-353cf6f9e512",
            "Neuroscience_of_Learning": "https://canvas.okstate.edu/files/26595495/download?download_frd=1&verifier=f84e0b5d-28a4-4096-a190-cdf3917912a3",
            "How_to_Study_Effectively": "https://canvas.okstate.edu/files/26595496/download?download_frd=1&verifier=a6dd7968-f362-4621-9035-d8a3c465ac9e",
            "What-is-biology": "https://canvas.okstate.edu/files/26595497/download?download_frd=1&verifier=79bba028-aeaf-46ce-9324-23272c8a3603",
            "Science_and_Peer_Review": "https://canvas.okstate.edu/files/26595498/download?download_frd=1&verifier=82a7dba8-2aa8-46bd-9e08-325ee79db83b",
            "The_cell_intro": "https://canvas.okstate.edu/files/26595499/download?download_frd=1&verifier=c830ed65-5005-4873-9597-0c87dff24adc",
            "Cholera_intro": "https://canvas.okstate.edu/files/26595501/download?download_frd=1&verifier=baa6e397-adfb-45bd-9cf6-71d33712ec66",
            "Cell_Membrane_Passive_Transport": "https://canvas.okstate.edu/files/26595503/download?download_frd=1&verifier=2f9897ec-7451-4d31-8aa7-15c5ccc022c9",
            "Cell_membrane_active_transport": "https://canvas.okstate.edu/files/26659338/download?download_frd=1&verifier=b5878574-fe7c-4005-9166-4035753ef5bd",
            "Cholera_explained": "https://canvas.okstate.edu/files/26595505/download?download_frd=1&verifier=e0da646c-ddbc-465e-b074-31f0fe06fcea",
        },
    },
}


def get_target(name):
    """Look up a target by name, with a clear error if it's missing or
    not fully configured yet."""
    if name not in TARGETS:
        valid = ", ".join(sorted(TARGETS))
        raise SystemExit(f"Error: unknown target '{name}'. Valid targets: {valid}")
    t = TARGETS[name]
    if not t.get("course_id"):
        raise SystemExit(
            f"Error: target '{name}' has no course_id set yet -- "
            f"fill it in in canvas_targets.py before building or uploading to it."
        )
    return t
