-- ==============================================================================
-- DATABASE: employee_db (PostgreSQL)
-- DESCRIPTION: Hệ thống quản lý nhân sự (HR)
-- ==============================================================================

CREATE SCHEMA IF NOT EXISTS employee_db;
SET search_path TO employee_db, public;

-- ------------------------------------------------------------------------------
-- 1. Bảng departments (Phòng ban)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS departments (
    department_id SERIAL PRIMARY KEY,
    department_code VARCHAR(50) NOT NULL UNIQUE,
    department_name VARCHAR(100),
    description VARCHAR(255),
    status VARCHAR(50) NOT NULL
);

-- ------------------------------------------------------------------------------
-- 2. Bảng positions (Chức danh)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS positions (
    position_id SERIAL PRIMARY KEY,
    position_code VARCHAR(50) NOT NULL UNIQUE,
    position_name VARCHAR(100),
    department_id INT NOT NULL,
    status VARCHAR(50) NOT NULL,
    
    CONSTRAINT fk_positions_department FOREIGN KEY (department_id) REFERENCES departments(department_id)
);

-- ------------------------------------------------------------------------------
-- 3. Bảng employees (Nhân viên)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS employees (
    employee_id SERIAL PRIMARY KEY,
    employee_code VARCHAR(50) NOT NULL UNIQUE,
    full_name VARCHAR(100),
    gender VARCHAR(20),
    date_of_birth DATE NOT NULL,
    phone VARCHAR(100),
    email VARCHAR(100),
    address VARCHAR(255),
    position_id INT NOT NULL,
    hire_date DATE NOT NULL,
    termination_date DATE,
    employment_type VARCHAR(100),
    status VARCHAR(50) NOT NULL,
    
    CONSTRAINT fk_employees_position FOREIGN KEY (position_id) REFERENCES positions(position_id)
);

-- ------------------------------------------------------------------------------
-- 4. Bảng employee_assignments (Phân công làm việc)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS employee_assignments (
    assignment_id SERIAL PRIMARY KEY,
    employee_id INT NOT NULL,
    assignment_type VARCHAR(100),
    store_id INT,       -- FK to retail_pos_db
    warehouse_id INT,   -- FK to warehouse_db
    factory_id INT,     -- FK to production_db
    start_date DATE NOT NULL,
    end_date DATE,
    status VARCHAR(50) NOT NULL,
    
    CONSTRAINT fk_assignments_employee FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
);

-- ------------------------------------------------------------------------------
-- 5. Bảng employee_shifts (Ca làm việc)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS employee_shifts (
    shift_id SERIAL PRIMARY KEY,
    employee_id INT NOT NULL,
    shift_date DATE NOT NULL,
    shift_type VARCHAR(100),
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    status VARCHAR(50) NOT NULL,
    
    CONSTRAINT fk_shifts_employee FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
);
