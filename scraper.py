from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import requests

# Create a new instance of the Chrome driver
driver = webdriver.Chrome()

# Navigate to the Slack URL
url = 'https://app.slack.com/client/TCKE4QSG5/'
driver.get(url)
time.sleep(30)

def capture_images():
    try:
        # Find the profile image container
        profile_container = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '/html/body/div[10]/div/div/div[2]/div[2]/div/div[2]/div[1]/div/div/div[1]/div/div/div[4]/button/div/div/div/div/span/span/img'))
        )
        
        # Get all profile images
        images = profile_container.find_elements(By.XPATH, './ancestor::div/div/div[4]/button/div/div/div/div/span/span/img')
        
        # Download first 9 images
        for i, img in enumerate(images[:9]):
            src = img.get_attribute('src')
            download_image(src, f"image_{i+1}.png")

        # Scroll down to load more messages
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)  # Short pause to allow new data to load

    except Exception as e:
        print(f"An error occurred: {e}")

def download_image(src, filename):
    # Request the image content
    response = requests.get(src)
    
    # Save the image to disk
    with open(filename, 'wb') as file:
        file.write(response.content)
    print(f"Downloaded image: {filename}")

# Perform an action on the element to view details
details_element = WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.CSS_SELECTOR, ".c-button-unstyled.p-avatar_stack--details"))
)
details_element.click()
time.sleep(5)

for _ in range(10):  # Adjust the range based on expected number of scrolls needed
    capture_images()

# Close the driver when done
driver.quit()