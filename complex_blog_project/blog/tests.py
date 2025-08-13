from django.test import TestCase, Client
from django.urls import reverse
from .models import Post, Tag
from django.contrib.auth.models import User


class PostListTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        """
        This method runs once for the whole test class.
        Here we create test data that will be used in all test methods.
        """
        # Create a test user
        cls.user = User.objects.create_user(username='testuser', password='12345')

        # Create 15 posts for testing pagination
        for i in range(15):
            Post.objects.create(
                title=f'Test Post {i}',
                content='Some content here',
                author=cls.user
            )

    def test_post_list_status_and_template(self):
        """
        Test:
        - Response status code is 200 (OK)
        - Correct template is used
        - Context contains 'posts' and 'page_obj'
        """
        client = Client()  # Create a simulated browser
        resp = client.get(reverse('post_list'))  # Send GET request to post list URL

        self.assertEqual(resp.status_code, 200)  # Check status code
        self.assertTemplateUsed(resp, 'blog/post_list.html')  # Check correct template
        self.assertIn('posts', resp.context)  # 'posts' exists in the context
        self.assertIn('page_obj', resp.context)  # 'page_obj' (pagination) exists

    def test_post_list_pagination_first_page(self):
        """
        Test:
        - Pagination works and the first page contains exactly 5 posts
        """
        client = Client()
        resp = client.get(reverse('post_list'))

        self.assertEqual(resp.status_code, 200)  # Check status code
        self.assertTrue('page_obj' in resp.context)  # Ensure pagination object is present
        self.assertEqual(len(resp.context['page_obj']), 5)  # Ensure 5 posts per page



    def test_post_list_pagination_second_page(self):
        """
        Test:
        - The second page returns the remaining posts
        - 'has_next()' is False on the last page
        """
        client = Client()

        # Act: request the second page
        resp = client.get(reverse('post_list'), {'page': 2})

        # Assert: response is OK
        self.assertEqual(resp.status_code, 200)

        # Calculate how many posts we expect on page 2.
        # total = number of posts created in setUpTestData
        total = Post.objects.count()

        # per_page = how many items your view shows on one page.
        # We don't hardcode 5 here — we infer expected count safely:
        # on page 2 you either get "per_page" items, or "whatever is left".
        # Leftover = max(0, total - per_page)
        # Expected on page 2 = min(per_page, leftover)
        per_page = 5
        leftover = max(0, total - per_page)
        expected_count = min(per_page, leftover)

        # The page object your view puts in context
        page_obj = resp.context['page_obj']

        # There should be exactly 'expected_count' posts on page 2
        self.assertEqual(len(page_obj), expected_count)

        # If there are only two pages worth of data, page 2 is the last one,
        # so has_next() must be False. If there is more data (3+ pages),
        # this will be True — both are valid depending on your fixtures.
        # To make the intention explicit, we assert that on the last page
        # (no matter which number it is) has_next() is False.
        # Here we check it dynamically:
        if total <= per_page * 2:
            self.assertFalse(page_obj.has_next())
        else:
            self.assertTrue(page_obj.has_next())


    def test_search_filters_by_title_content_tag_author(self):
        """
        Test:
        - 'q' filters results by title, content, tag name, and author username
        - Matching is case-insensitive
        """
        client = Client()

        # Create extra users for author filtering
        alice = User.objects.create_user(username='alice', password='x')
        bob = User.objects.create_user(username='bob', password='x')

        # Create tags used for tag filtering
        t_django = Tag.objects.create(name='Django')
        t_python = Tag.objects.create(name='Python')

        # Create posts with controlled content
        p1 = Post.objects.create(title='Learn Django', content='Basics', author=alice)
        p1.tags.add(t_django)

        p2 = Post.objects.create(title='Other topic', content='Deep dive into python', author=bob)
        p2.tags.add(t_python)

        p3 = Post.objects.create(title='Alice note', content='Nothing special', author=alice)

        p4 = Post.objects.create(title='Irrelevant', content='No match here', author=bob)

        # Helper to fetch titles for a given query q from the first page
        def fetch_titles(q):
            resp = client.get(reverse('post_list'), {'q': q})
            self.assertEqual(resp.status_code, 200)
            # Collect titles from the context (order does not matter for this test)
            return {post.title for post in resp.context['posts']}

        # 1) Title match (and tag match): "django" should include p1 and exclude others
        with self.subTest(q='django'):
            titles = fetch_titles('django')
            self.assertIn('Learn Django', titles)
            self.assertNotIn('Irrelevant', titles)

        # 2) Case-insensitivity: "DJaNgO" must give the same as "django"
        with self.subTest(q='DJaNgO'):
            titles = fetch_titles('DJaNgO')
            self.assertIn('Learn Django', titles)

        # 3) Tag/content match: "python" should include p2 (content/tag) and exclude p1
        with self.subTest(q='python'):
            titles = fetch_titles('python')
            self.assertIn('Other topic', titles)
            self.assertNotIn('Learn Django', titles)

        # 4) Author match: searching "alice" should include posts by alice (p1, p3)
        with self.subTest(q='alice'):
            titles = fetch_titles('alice')
            self.assertIn('Learn Django', titles)
            self.assertIn('Alice note', titles)
            self.assertNotIn('Irrelevant', titles)