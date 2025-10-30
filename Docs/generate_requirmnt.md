# 🧾 Generate `requirements.txt` Using `pipreqs`

This guide explains how to create a **project-specific** `requirements.txt` file using [`pipreqs`](https://pypi.org/project/pipreqs/).

Unlike `pip freeze`, `pipreqs` only includes **packages actually used** in your project (based on import statements).

---

## 📦 Installation

```bash
pip install pipreqs
```

---

## 📁 Navigate to Your Project Directory

Move to the root folder of your Python project:

```bash
cd /path/to/your/project
```

---

## ⚙️ Generate `requirements.txt`

Create the requirements file in the current directory:

```bash
pipreqs .
```

* `.` represents the current directory.
* Replace it with another path if needed.

---

## 🔄 Overwrite an Existing File (Optional)

If `requirements.txt` already exists and you want to replace it:

```bash
pipreqs . --force
```

---

## 💾 Save to a Custom Location (Optional)

To save the file to a specific path or name:

```bash
pipreqs . --savepath /path/to/desired/file.txt
```

---

## 👀 Preview Detected Packages (Optional)

To view the detected dependencies without creating the file:

```bash
pipreqs . --print
```

---

## ✅ Why Use `pipreqs`?

* 📦 Includes only packages actually used in your project
* 🧹 Avoids environment clutter from unused dependencies
* ⚡ Ideal for clean, reproducible project sharing on GitHub

---

## 📥 Install Dependencies

Once you’ve generated your `requirements.txt`, others can install all dependencies by running:

```bash
pip install -r requirements.txt
```


#Python #pipreqs #Requirements #DependencyManagement
