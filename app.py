import streamlit as st
import sqlite3
import pandas as pd


def get_data(query, params=None):
    conn = sqlite3.connect("food_management.sqlite")
    if params:
        df = pd.read_sql_query(query, conn, params=params)
    else:
        df = pd.read_sql_query(query, conn)
    conn.close()
    return df

st.set_page_config(page_title="Food_Wastage_Management_Systems", layout="wide")

st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Project Introduction", "View Tables", "CRUD Operations", "SQL Queries", "Creator Info"])

if page == "Project Introduction":
    st.title("Food Wastage Management System")
    st.markdown(""" 
    Welcome to the **Food Wastage Management System**!

    This project helps manage surplus food and reduce wastage by connecting **providers** with those in need.

    - 🏢 **Providers:** Restaurants, households, and businesses list surplus food.
    - 🧑‍🤝‍🧑 **Receivers:** NGOs and individuals claim available food.
    - 📍 **Geolocation:** Helps locate nearby food efficiently.
    - 📊 **SQL Analysis:** Gain powerful insights from stored data.

    Let's work together to minimize food waste and make a difference!
    """)

elif page == "View Tables":
    conn = sqlite3.connect('food_management.sqlite')
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]

    selected_table = st.selectbox("Select a table to view:", tables)

    if selected_table:
       query = f"SELECT * FROM {selected_table} "
       df = pd.read_sql_query(query, conn)
       st.dataframe(df)



elif page == "CRUD Operations":
    conn = sqlite3.connect('food_management.sqlite') 
    cursor = conn.cursor()

    def get_tables():
     cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
     tables = cursor.fetchall()
     return [t[0] for t in tables]

    st.title("Manage Food Data")
    tables = get_tables()

    if not tables:
        st.warning("No tables found in the database.")
    else:
        selected_table = st.selectbox("Select a table to perform CRUD operations", tables)

        
    st.subheader(f"Data in {selected_table}")
    df = pd.read_sql_query(f"SELECT * FROM {selected_table}", conn)
    st.dataframe(df)

    crud_action = st.radio("Select Operation", ["Insert", "Update", "Delete"])


    if crud_action == "Insert":
         st.markdown("### Add New Record")
         cursor.execute(f"PRAGMA table_info({selected_table})")
         columns_info = cursor.fetchall()
         columns = [col[1] for col in columns_info]
         pk_column = next((col[1] for col in columns_info if col[5] == 1), None)


         new_data = {}
         for col in columns:
            new_data[col] = st.text_input(f"Enter value for {col}", key=f"add_{col}")

         if st.button("Insert Record"):
            values = tuple(new_data[col] for col in columns)
            placeholders = ",".join(["?"] * len(values))
            query = f"INSERT INTO {selected_table} ({', '.join(columns)}) VALUES ({placeholders})"
            try:
                cursor.execute(query, values)
                conn.commit()
                st.success("Record inserted successfully.")
            except Exception as e:
                st.error(f"Failed to insert record: {e}")
    elif crud_action == "Update":
            st.markdown("### Update Record")
            cursor.execute(f"PRAGMA table_info({selected_table})")
            columns_info = cursor.fetchall()
            columns = [col[1] for col in columns_info]
            pk_column = next((col[1] for col in columns_info if col[5] == 1), None)

            pk_column = None
            for col_info in columns_info:
                if col_info[5] == 1:
                 pk_column = col_info[1]
                 break
            if pk_column:
                ids = pd.read_sql_query(f"SELECT {pk_column} FROM {selected_table}", conn)[pk_column].tolist()
                selected_id = st.selectbox(f"Select {pk_column} to update", ids)
                if selected_id:
                    row_data = pd.read_sql_query(f"SELECT * FROM {selected_table} WHERE {pk_column} = ?", conn, params=(selected_id,))
                    if not row_data.empty:
                        updated_values = {}
                        for col in row_data.columns:
                            if col == pk_column:
                                st.text(f"{col} (Primary Key): {row_data.at[0, col]}")
                                continue
                            updated_values[col] = st.text_input(f"{col}", value=str(row_data.at[0, col]), key=f"update_{col}")

                        if st.button("Update"):
                            set_clause = ", ".join([f"{col} = ?" for col in updated_values])
                            values = list(updated_values.values())
                            values.append(selected_id)
                            update_query = f"UPDATE {selected_table} SET {set_clause} WHERE {pk_column} = ?"
                            try:
                                cursor.execute(update_query, values)
                                conn.commit()
                                st.success("Record updated successfully.")
                            except Exception as e:
                                st.error(f"Update failed: {e}")
            else:
                st.warning("Primary key not found. Cannot perform update.")

    elif crud_action == "Delete":
        st.markdown("### Delete Record")

    
        cursor.execute(f"PRAGMA table_info({selected_table})")
        columns_info = cursor.fetchall()
        columns = [col[1] for col in columns_info]

    
        selected_column = st.selectbox("Select column to filter by", columns)

    
        values_df = pd.read_sql_query(f"SELECT DISTINCT {selected_column} FROM {selected_table}", conn)
        values = values_df[selected_column].dropna().tolist()

    
        selected_value = st.selectbox(f"Select value from column '{selected_column}'", values, key="delete_value")

        if st.button("Delete"):
            try:
                cursor.execute(f"DELETE FROM {selected_table} WHERE {selected_column} = ?", (selected_value,))
                conn.commit()
                st.success(f"Records with {selected_column} = '{selected_value}' deleted.")
                #st.experimental_rerun()
            except Exception as e:
                st.error(f"Deletion failed: {e}")
    
        st.markdown("#### Records to be deleted:")
        preview_df = pd.read_sql_query(
            f"SELECT * FROM {selected_table} WHERE {selected_column} = ?", conn, params=(selected_value,)
        )
        st.dataframe(preview_df)

elif page == "SQL Queries":
    st.title("📋 SQL Query Results")
    queries = {"1.How many food providers are there in each city":"SELECT City, COUNT(*) AS provider_count FROM providers GROUP BY City ORDER BY provider_count",
               "2.How many food receivers are there in each city":"SELECT City, COUNT(*) AS receivers_count FROM receivers GROUP BY City ORDER BY receivers_count",
               "3.Which type of food provider (restaurant, grocery store, etc.) contributes the most food":"SELECT type, count(*) AS Total_provided FROM providers GROUP BY Type order by Total_provided desc limit 1",    
               "4.What is the contact information of food providers in a specific city":"SELECT city, contact FROM providers where city = 'West Dawn' ",
               "5.Which receivers have claimed the most food":"SELECT type, count(*) AS total_claimed FROM receivers GROUP BY Type order by total_claimed desc limit 1",        
               "6.What is the total quantity of food available from all providers":"select sum(quantity) as Total_food_quantity from Food_listings",
               "7.Which city has the highest number of food listings":"SELECT Location, COUNT(*) AS highest_listing FROM food_listings GROUP BY Location ORDER BY highest_listing DESC LIMIT 2", 
               "8.What are the most commonly available food types":"SELECT FOOD_TYPE, count(*) Commanly_available FROM food_listings GROUP BY fOOD_TYPE order by commanly_available desc limit 1" ,
               "9.How many food claims have been made for each food item":"SELECT Food_ID, COUNT(*) AS claim_count FROM claims GROUP BY Food_ID ORDER BY claim_count DESC",
               "10.Which provider has had the highest number of successful food claims":"select fl.provider_ID, count(*) AS successful_claims from claims c JOIN food_listings fl ON c.food_id = fl.food_id WHERE c.status ='Completed' Group by fl.provider_ID Order by successful_claims desc  limit 1",
               "11.What percentage of food claims are completed vs. pending vs. canceled":"SELECT Status, COUNT(*) * 100.0 / (SELECT COUNT(*) FROM claims) AS percentage FROM claims GROUP BY Status",
               "12.What is the average quantity of food claimed per receiver":"SELECT Receiver_ID, AVG(fl.Quantity) AS avg_quantity_claimed FROM claims c JOIN food_listings fl ON c.Food_ID = fl.Food_ID GROUP BY Receiver_ID",    
               "13.Which meal type (breakfast, lunch, dinner, snacks) is claimed the most":"select meal_type, count(*) As Most_claimed_type from food_listings group by meal_type order by Most_claimed_type desc limit 1",
               "14.What is the total quantity of food donated by each provider":"SELECT Provider_ID, SUM(Quantity) AS total_quantity_donated FROM food_listings GROUP BY Provider_ID ORDER BY total_quantity_donated DESC"                        
                                                                          
                } 

    selected_query = st.selectbox("Choose a Query", list(queries.keys()))
    query_result = get_data(queries[selected_query])

    st.write("### Query Result:")
    st.dataframe(query_result)

elif page == "Creator Info":
    st.title("👩‍💻 Creator of this Project")
    st.write(" **Developed by:** Karthika ")
    st.write(" **Skills:** Python, SQL, Data Analysis,Streamlit, Pandas" )
