  ABOUT
  ------------
  This application is intended to be used after copying everything from a
  photoshoot to your computer. It will help sort and organize the pictures
  into different folders before taking them to your editing software.
  
  The code for this project was writted exlusively by Claude Code.
  The creation of every feature was directed by Sam Rodgers.

================================================================================
  PhotoPicker Toolkit
================================================================================

  REQUIREMENTS
  ------------
  Python 3.x, Pillow, and exifread:
      python --version
      pip install Pillow exifread

  GRAPHICAL LAUNCHER (recommended — no terminal required)
  --------------------------------------------------------
  Double-click launch.bat to open the dashboard. No terminal will appear.

  The dashboard includes a step-by-step tutorial (click the ? button).
  Each tool card has Browse buttons that open a file picker — click any photo
  inside the folder you want to select, and the folder path is filled in
  automatically. Output folder pickers let you create a new folder.

  If double-clicking launch.bat does nothing, Python may not be installed.
  Install Python from https://www.python.org/downloads/ (tick "Add to PATH"),
  then run: pip install Pillow exifread

  FOR DEVELOPERS — running from terminal:
      python app.py          (with terminal window)
      pythonw app.py         (no terminal window)

  SHARING WITH NON-TECHNICAL USERS — creating a standalone .exe:
      pip install pyinstaller
      pyinstaller --onedir --windowed --name PhotoPicker app.py
  This creates dist/PhotoPicker/PhotoPicker.exe which runs on any Windows PC
  without Python installed. Share the entire dist/PhotoPicker/ folder.

  Pillow is used by photopicker.py for image display.
  exifread is used by rename_by_date.py to read EXIF dates from JPEG and RAW files.
  All other scripts use only the Python standard library.


================================================================================
  photopicker.py  —  Browse and flag photos interactively
================================================================================

  USAGE
      python photopicker.py <folder>
      python photopicker.py <folder> --output <output_folder>
      python photopicker.py <folder> --move

  ARGUMENTS
      <folder>            Folder of images to browse. Defaults to current dir.
      --output <folder>   Where to send flagged photos. Defaults to <folder>/selected/
      --move              Move flagged photos instead of copying them.

  KEYS
      Left / Right        Navigate between photos
      Space, F, or K      Flag current photo as "keep" and advance
      U                   Unflag current photo
      Q or Escape         Quit and save all flagged photos to the output folder

  NOTES
      - Nothing is written to disk until you quit.
      - The output folder is created automatically if it doesn't exist.
      - Supported formats: JPG, PNG, GIF, BMP, TIFF, WebP

  EXAMPLES
      python photopicker.py "D:\Photos\Shoot1"
      python photopicker.py "D:\Photos\Shoot1" --output "D:\Photos\Picks"
      python photopicker.py "D:\Photos\Picks" --output "D:\Photos\Finals"


================================================================================
  separate_raws.py  —  Split a mixed folder into raw/, jpeg/, and video/ subfolders
================================================================================

  USAGE
      python separate_raws.py <folder>
      python separate_raws.py <folder> --copy

  Moves all recognized files in <folder> into subfolders created inside it:
      <folder>/raw/    — camera RAW files
      <folder>/jpeg/   — JPEG and other preview/export formats
      <folder>/video/  — video files

  By default files are MOVED. Pass --copy to copy instead and leave originals.
  Files with unrecognized extensions are left in place and listed at the end.

  SUPPORTED RAW FORMATS BY BRAND
      Canon       .CRW .CR2 .CR3
      Nikon       .NEF .NRW
      Sony        .ARW .SRF .SR2
      Fujifilm    .RAF
      Olympus     .ORF
      Panasonic   .RW2
      Pentax      .PEF .PTX
      Samsung     .SRW
      Leica       .RWL .DNG
      Hasselblad  .3FR .FFF
      Phase One   .IIQ
      Sigma       .X3F
      Kodak       .DCR .KDC
      Minolta     .MRW
      GoPro       .GPR
      + Adobe DNG (.DNG) used by many brands as a universal raw format

  SUPPORTED VIDEO FORMATS
      .MP4 .MOV .AVI .MTS .M2TS .MXF .MKV .WMV .M4V .3GP .R3D .BRAW .ARI

  EXAMPLE
      python separate_raws.py "D:\Photos\Shoot1"

      Before:  Shoot1/  IMG_0001.CR3  IMG_0001.JPG  IMG_0001.MP4
      After:   Shoot1/raw/    IMG_0001.CR3
               Shoot1/jpeg/   IMG_0001.JPG
               Shoot1/video/  IMG_0001.MP4


================================================================================
  photopicker.py  —  Browse and flag photos interactively
================================================================================

  (see above)


================================================================================
  diff_folders.py  —  Copy files that are in one folder but not another
================================================================================

  USAGE
      python diff_folders.py <folder_a> <folder_b> <output_folder>

  Copies every file from folder_a whose filename does NOT appear in folder_b
  into output_folder. Useful for collecting the photos you rejected during a
  PhotoPicker session.

  EXAMPLE
      After running photopicker.py, Shoot1/jpeg/picks/ has your kept photos.
      To collect everything you didn't pick:

          python diff_folders.py "D:\Photos\Shoot1\jpeg" "D:\Photos\Shoot1\jpeg\picks" "D:\Photos\Shoot1\jpeg\rejected"


================================================================================
  get_raws.py  —  Fetch RAW files (and XMP sidecars) matching a set of previews
================================================================================

  USAGE
      python get_raws.py <jpeg_folder> <raw_folder> <output_folder>

  For each image in jpeg_folder, finds the file with the same base name
  (ignoring extension) in raw_folder and copies it to output_folder.
  XMP sidecar files are copied automatically alongside their RAW files.
  Both IMG_1234.xmp and IMG_1234.CR3.xmp naming styles are supported.

  EXAMPLE
      python get_raws.py "D:\Photos\Shoot1\finals" "D:\Photos\Shoot1\raw" "D:\Photos\Shoot1\finals_raw"

      If finals/ has IMG_1234.jpg and raw/ has IMG_1234.CR3 + IMG_1234.xmp,
      then finals_raw/ will contain IMG_1234.CR3 and IMG_1234.xmp.


================================================================================
  verify_copy.py  —  Confirm files copied to a destination without corruption
================================================================================

  USAGE
      python verify_copy.py <source_folder> <dest_folder>

  Computes an MD5 checksum for every file in source_folder and compares it to
  the matching file in dest_folder. Reports any missing or mismatched files.
  Run this after copying your finals to an external drive, before deleting
  the originals. Exits with code 1 if any problems are found.

  EXAMPLE
      python verify_copy.py "D:\Photos\Shoot1\finals_raw" "E:\Handoff\finals_raw"


================================================================================
  rename_by_date.py  —  Rename files using their EXIF shoot date
================================================================================

  USAGE
      python rename_by_date.py <folder>
      python rename_by_date.py <folder> --dry-run

  Renames image files to YYYY-MM-DD_HHMMSS.ext using the EXIF DateTimeOriginal
  tag. If two files share the exact same timestamp, a counter is appended
  (_2, _3, ...). Files with no EXIF date fall back to file modification time
  and are flagged in the output.

  Use --dry-run to preview all renames without making any changes.
  Supports JPEG and all major RAW formats. Requires: pip install exifread

  EXAMPLE
      python rename_by_date.py "D:\Photos\Shoot1\finals_raw" --dry-run
      python rename_by_date.py "D:\Photos\Shoot1\finals_raw"

      Before:  IMG_1234.CR3  IMG_1589.CR3
      After:   2024-07-15_143022.CR3  2024-07-15_143028.CR3


================================================================================
  TYPICAL FULL WORKFLOW
================================================================================

  1. Separate the mixed RAW+JPEG+video folder from your memory card:
         python separate_raws.py "D:\Photos\Shoot1"
         → creates Shoot1/raw/  Shoot1/jpeg/  Shoot1/video/

  2. Browse the JPEGs and pick the ones you want:
         python photopicker.py "D:\Photos\Shoot1\jpeg" --output "D:\Photos\Shoot1\picks"

  3. (Optional) Do a second pass to narrow down further:
         python photopicker.py "D:\Photos\Shoot1\picks" --output "D:\Photos\Shoot1\finals"

  4. Grab the RAW files (and any XMP sidecars) for the photos you kept:
         python get_raws.py "D:\Photos\Shoot1\finals" "D:\Photos\Shoot1\raw" "D:\Photos\Shoot1\finals_raw"

  5. (Optional) Rename RAW files by shoot date before handing off:
         python rename_by_date.py "D:\Photos\Shoot1\finals_raw"

  6. Copy finals_raw/ to your external drive or handoff location.

  7. Verify the copy before deleting originals:
         python verify_copy.py "D:\Photos\Shoot1\finals_raw" "E:\Handoff\finals_raw"

  8. (Optional) See what JPEGs you rejected in step 2:
         python diff_folders.py "D:\Photos\Shoot1\jpeg" "D:\Photos\Shoot1\picks" "D:\Photos\Shoot1\rejected"
