import streamlit as st
from a7do.profiles import WorldProfiles, PlaceProfile, PersonProfile, AnimalProfile, ObjectProfile
from a7do.homeplot import generate_default_home

st.set_page_config(page_title="World Profile", layout="wide")

if "world" not in st.session_state:
    st.session_state.world = WorldProfiles()

world = st.session_state.world

st.title("🌍 World Profile (Observer-only)")

left, right = st.columns([1, 1])

with left:
    st.subheader("Home scaffold (seeded)")
    world.home_seed = st.number_input("Home seed", min_value=1, value=int(world.home_seed), step=1)

    if st.button("Generate / Regenerate HomePlot (scaffold)"):
        home = generate_default_home(int(world.home_seed))
        # write rooms into places (as profiles)
        world.places = {}
        for rn, room in home.rooms.items():
            world.places[rn] = PlaceProfile(
                name=rn,
                level=0 if rn == "hall" else 1,
                purpose="room",
                features=room.features,
                wall_colour=room.wall_colour,
                windows=room.windows,
                sounds=["quiet"] if rn.startswith("bedroom") else ["house hum"],
                smells=["clean"] if rn == "bathroom" else ["neutral"]
            )
        world.home_generated = True
        st.session_state.homeplot = home
        st.success("HomePlot generated. Rooms are now authoritative places.")
        st.rerun()

    st.divider()
    st.subheader("People (must include Mum + Dad to unlock learning)")
    with st.form("add_person"):
        name = st.text_input("Name")
        role = st.selectbox("Role", ["mum", "dad", "caregiver", "other"])
        if st.form_submit_button("Add person") and name:
            world.people[name] = PersonProfile(name=name, role=role)
            st.rerun()

    st.subheader("Animals")
    with st.form("add_animal"):
        name = st.text_input("Animal name")
        species = st.text_input("Species (dog/cat/etc)")
        if st.form_submit_button("Add animal") and name and species:
            world.animals[name] = AnimalProfile(name=name, species=species, sounds=["bark"] if species.lower()=="dog" else [])
            st.rerun()

    st.subheader("Objects")
    with st.form("add_object"):
        name = st.text_input("Object name (e.g., ball, toolbox, tool)")
        category = st.selectbox("Category", ["toy", "furniture", "tool", "container", "other"])
        attrs = st.text_input("Attributes (comma) e.g. red, round")
        aff = st.text_input("Affordances (comma) e.g. roll, throw, catch")
        if st.form_submit_button("Add object") and name:
            world.objects[name] = ObjectProfile(
                name=name,
                category=category,
                attributes=[a.strip() for a in attrs.split(",") if a.strip()],
                affordances=[a.strip() for a in aff.split(",") if a.strip()],
            )
            st.rerun()

with right:
    st.subheader("Snapshot")
    st.json(world.snapshot())

    st.subheader("HomePlot preview (if generated)")
    homeplot = st.session_state.get("homeplot")
    if homeplot:
        st.write("Rooms:")
        for rn, room in homeplot.rooms.items():
            st.write(f"- **{rn}**: {room.width}×{room.length}m, walls={room.wall_colour}, windows={room.windows}, features={', '.join(room.features)}")
        st.write("Doors:")
        for a, b in homeplot.doors:
            st.write(f"- {a} ↔ {b}")
    else:
        st.info("No HomePlot yet. Generate one.")